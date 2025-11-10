from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.views.decorators.cache import never_cache, cache_control
from decimal import Decimal
import uuid
import boto3
import smtplib
from email.mime.text import MIMEText
from django.conf import settings
from functools import wraps
from django.contrib.auth import logout
from .dynamo_users import add_user_to_dynamo, verify_user_credentials
from .models import Room, Booking, RoomImage, Profile
from .forms import BookingForm, RegisterForm, LoginForm
from .dynamo_rooms import (
    get_all_rooms,
    add_room_to_dynamo,
    get_room_from_dynamo,
    update_room_in_dynamo,
    delete_room_from_dynamo,
    update_room_images_in_dynamo
)
from .aws_utils import insert_booking_to_dynamodb
from datetime import datetime
from accounts import views
from accounts.views import login_required_dynamo, manager_required
from staywiselib.pricing import calculate_final_price 
from decimal import Decimal
from email.mime.multipart import MIMEMultipart
from boto3.dynamodb.conditions import Attr


# ======================================================
# 🏠 Room Listing (DynamoDB)
# ======================================================
@never_cache
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@login_required_dynamo
def room_list(request):
    print("🔹 Active Session Cookie:", settings.SESSION_COOKIE_NAME)

    rooms = get_all_rooms()
    return render(request, 'accommodation/room_list.html', {'rooms': rooms})


# ======================================================
# 🏡 Room Booking (DynamoDB)
# ======================================================
from decimal import Decimal
import uuid
from datetime import datetime

@login_required_dynamo
def book_room(request, room_id):
    # ✅ Fetch room details from DynamoDB
    room = get_room_from_dynamo(room_id)
    if not room:
        messages.error(request, "Room not found.")
        return redirect('room_list')

    # ✅ Room availability check
    if not room.get('available', True):
        return render(request, 'accommodation/room_full.html', {'room': room})

    if request.method == 'POST':
        form = BookingForm(request.POST)
        if form.is_valid():
            people = form.cleaned_data['people']
            days = form.cleaned_data['days']
            checkin_date = form.cleaned_data.get('checkin_date')
            checkout_date = form.cleaned_data.get('checkout_date')

            # ✅ Validate capacity
            if people > int(room['capacity']):
                form.add_error('people', f"Only {room['capacity']} people allowed for this room.")
                return render(request, 'accommodation/book_room.html', {'room': room, 'form': form})

            # ✅ Base price
            base_price = Decimal(str(room['price'])) * Decimal(days) * Decimal(people)

            # ✅ Use enhanced pricing library (Festival + Weekend + Long-Stay)
            price_info = calculate_final_price(base_price, event="Diwali", days=days)
            final_price = Decimal(str(price_info["final_price"]))
            discount_percent = Decimal(str(price_info["total_discount_percent"]))
            discount_amount = Decimal(str(price_info["total_discount_amount"]))
            discount_reason = price_info.get("discount_reason")

            # ✅ Collect payment method
            payment_method = request.POST.get('payment_method', 'Cash on Arrival')

            # ✅ Booking record
            booking_data = {
                'booking_id': str(uuid.uuid4()),
                'room_id': room_id,
                'room_name': room['name'],
                'name': form.cleaned_data['name'],
                'email': form.cleaned_data['email'],
                'days': days,
                'people': people,
                'checkin_date': str(checkin_date),
                'checkout_date': str(checkout_date),
                'price_before_discount': base_price,
                'final_price': final_price,
                'discount_percent': discount_percent,
                'discount_amount': discount_amount,
                'discount_reason': discount_reason,
                'payment_method': payment_method,
                'payment_status': 'Unpaid',
                'booked_on': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'booked_by_email': request.session['user']['email'],
                
            }

            # ✅ Store booking in DynamoDB
            insert_booking_to_dynamodb(booking_data)

            # ✅ Email confirmation
            send_user_email(booking_data)

            # ✅ Update room capacity
            new_capacity = int(room['capacity']) - people
            update_room_in_dynamo(room_id, room['name'], max(new_capacity, 0), room['price'])

            messages.success(request, f"Booking confirmed! You saved €{discount_amount} ({discount_percent}% off)")
            response = render(request, 'accommodation/booking_success.html', {'booking': booking_data})
            list(messages.get_messages(request))  # clear messages
            return response

    else:
        form = BookingForm()

    return render(request, 'accommodation/book_room.html', {'room': room, 'form': form})


# ======================================================
# 📊 Manager Dashboard
# ======================================================
# @never_cache
# @login_required_dynamo
# @manager_required
# def manager_dashboard(request):
#     rooms = get_all_rooms()
#     bookings = Booking.objects.all()  # Optional: Still from SQLite
#     return render(request, 'accommodation/manager_dashboard.html', {'rooms': rooms, 'bookings': bookings})




from datetime import datetime

def parse_date(date_str):
    """Safely convert DynamoDB date string (YYYY-MM-DD) to datetime for sorting."""
    try:
        return datetime.strptime(date_str, "%Y-%m-%d")
    except Exception:
        return datetime.min


@never_cache
@login_required_dynamo
@manager_required
def manager_dashboard(request):
    print("🔹 Active Session Cookie:", settings.SESSION_COOKIE_NAME)

    # Fetch data from DynamoDB
    rooms = get_all_rooms() or []
    bookings = get_all_bookings_from_dynamo() or []

    # 🧩 Safely count full rooms (capacity == 0)
    total_rooms = len(rooms)
    fully_booked_rooms = sum(1 for r in rooms if r and int(r.get('capacity', 0)) == 0)
    total_bookings = len(bookings)

    # 🧠 Sort bookings by date (most recent first)
    from datetime import datetime
    def parse_date(b):
        d = b.get('booked_on')
        try:
            return datetime.strptime(d, "%Y-%m-%d %H:%M:%S") if d else datetime.min
        except Exception:
            return datetime.min

    bookings_sorted = sorted(bookings, key=parse_date, reverse=True)

    # ✅ Room name mapping (safe against missing values)
    room_map = {}
    for r in rooms:
        if not r:
            continue
        rid = r.get('room_id')
        name = r.get('name', 'Unknown')
        if rid:
            room_map[rid] = name

    # ✅ Attach readable room names to bookings
    for b in bookings_sorted:
        room_id = b.get('room_id')
        if room_id in room_map:
            b['room_name'] = room_map[room_id]
        else:
            b['room_name'] = f"Room ({str(room_id)[:6]})"

        # 🔹 Convert Decimal fields to float for safe template math
        try:
            if 'price_before_discount' in b:
                b['price_before_discount'] = float(b['price_before_discount'])
        except Exception:
            b['price_before_discount'] = 0.0

        try:
            if 'final_price' in b:
                b['final_price'] = float(b['final_price'])
        except Exception:
            b['final_price'] = 0.0

    # ✅ Summary stats for UI
    summary = {
        'total_rooms': total_rooms,
        'fully_booked_rooms': fully_booked_rooms,
        'total_bookings': total_bookings,
    }

    return render(request, 'accommodation/manager_dashboard.html', {
        'rooms': rooms,
        'bookings': bookings_sorted,
        'summary': summary
    })



# ======================================================
# ➕ Add Room (DynamoDB + S3)
# ======================================================
@never_cache
@login_required_dynamo
@manager_required
def add_room(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        capacity = request.POST.get('capacity')
        price = request.POST.get('price')
        images = request.FILES.getlist('images')

        s3 = boto3.client('s3', region_name='us-east-1')
        bucket = settings.AWS_STORAGE_BUCKET_NAME
        image_urls = []

        for image in images:
            key = f"rooms/{uuid.uuid4()}_{image.name}"
            s3.upload_fileobj(
                image,
                bucket,
                key,
                ExtraArgs={'ContentType': image.content_type}
            )
            image_urls.append(f"https://{bucket}.s3.amazonaws.com/{key}")

        add_room_to_dynamo(name, capacity, price, image_urls)
        messages.success(request, "Room added successfully with images!")
        return redirect('manager_dashboard')

    return render(request, 'accommodation/add_room.html')


# ======================================================
# ✏️ Edit Room (DynamoDB + S3)
# ======================================================
@never_cache
@login_required_dynamo
@manager_required
def edit_room(request, room_id):
    room = get_room_from_dynamo(room_id)
    if not room:
        messages.error(request, "Room not found in DynamoDB.")
        return redirect('manager_dashboard')

    if request.method == 'POST':
        name = request.POST.get('name')
        capacity = request.POST.get('capacity')
        price = request.POST.get('price')
        images = request.FILES.getlist('images')

        update_room_in_dynamo(room_id, name, capacity, price)

        if images:
            s3 = boto3.client('s3', region_name='us-east-1')
            bucket = settings.AWS_STORAGE_BUCKET_NAME
            image_urls = []
            for image in images:
                key = f"rooms/{uuid.uuid4()}_{image.name}"
                s3.upload_fileobj(
                    image,
                    bucket,
                    key,
                    ExtraArgs={'ContentType': image.content_type}
                )
                image_urls.append(f"https://{bucket}.s3.amazonaws.com/{key}")

            update_room_images_in_dynamo(room_id, image_urls)

        messages.success(request, "Room updated successfully!")
        return redirect('manager_dashboard')

    return render(request, 'accommodation/edit_room.html', {'room': room})


# ======================================================
# ❌ Delete Room
# ======================================================
@never_cache
@login_required_dynamo
@manager_required
def delete_room(request, room_id):
    try:
        delete_room_from_dynamo(room_id)
        messages.success(request, "Room deleted successfully!")
    except Exception as e:
        messages.error(request, f"Error deleting room: {e}")

    return redirect('manager_dashboard')


# ======================================================
# 🖼️ Delete Room Image (S3 + DynamoDB)
# ======================================================
@login_required_dynamo
@manager_required
def delete_room_image(request, image_id):
    try:
        s3 = boto3.client('s3', region_name='us-east-1')
        bucket = settings.AWS_STORAGE_BUCKET_NAME

        key = f"rooms/{image_id}"
        s3.delete_object(Bucket=bucket, Key=key)

        update_room_images_in_dynamo(image_id, remove=True)
        messages.success(request, "Image deleted successfully!")
    except Exception as e:
        messages.error(request, f"Error deleting image: {e}")

    return redirect('manager_dashboard')


# ======================================================
# ✉️ Email Notification (SMTP)
# ======================================================
def send_user_email(booking_data):
    """Send booking confirmation email to the customer via Gmail SMTP."""

    sender = "shri2178499@gmail.com"           # ✅ Your Gmail address
    password = "reynldypshnzrxfr"              # ✅ App password
    recipient = booking_data.get("email")

    if not recipient:
        print("❌ No recipient email found in booking_data")
        return

    # ✅ Extract booking info safely
    name = booking_data.get("name", "Customer")
    room_name = booking_data.get("room_name", "Room")
    base_price = booking_data.get("price_before_discount", 0)
    final_price = booking_data.get("final_price", 0)
    discount_percent = booking_data.get("discount_percent", 0)
    discount_reason = booking_data.get("discount_reason", "-")
    payment_method = booking_data.get("payment_method", "N/A")
    payment_status = booking_data.get("payment_status", "Unpaid")
    booked_on = booking_data.get("booked_on", "-")

    # ✅ Dynamic subject
    subject = f"🎉 StayWise Booking Confirmed - {room_name}"

    # ✅ Customer-friendly body
    body = f"""
Hello {name},

✅ Your booking has been confirmed successfully!

🏠 Room: {room_name}
💰 Base Price: €{base_price}
💸 Final Price: €{final_price}
🎁 Discount: {discount_percent}% ({discount_reason})
💳 Payment Method: {payment_method}
📄 Payment Status: {payment_status}
📅 Booked On: {booked_on}

Thank you for booking with StayWise! 🏡
We look forward to hosting you soon.
"""

    # ✅ Create MIME message
    msg = MIMEMultipart()
    msg["From"] = sender
    msg["To"] = recipient
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))

    try:
        print(f"📤 Connecting to Gmail SMTP for {recipient}...")
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(sender, password)
            server.send_message(msg)
        print(f"✅ Booking confirmation email sent successfully to: {recipient}")
        print(f"📧 Subject: {subject}")
        print(f"💬 Preview:\n{body}")

    except smtplib.SMTPAuthenticationError:
        print("❌ Authentication failed — check your Gmail App Password setup.")
    except Exception as e:
        print("❌ Error sending user email:", e)
def get_all_bookings_from_dynamo():
    """Fetch all booking records from DynamoDB."""
    dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
    table = dynamodb.Table('Bookings')
    response = table.scan()
    return response.get('Items', [])
    
    
    
@login_required_dynamo
def my_bookings(request):
    # 🛑 If not logged in, redirect to login
    if 'user' not in request.session:
        return redirect('login_user')

    # ✅ Use email from session (not Django user)
    user_email = request.session['user']['email']

    dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
    table = dynamodb.Table('Bookings')

    # 🧩 Fetch bookings belonging to this user
    response = table.scan()
    all_bookings = response.get('Items', [])

    # Filter only the logged-in user's bookings
    user_bookings = [b for b in all_bookings if b.get('booked_by_email') == user_email]


    # ✅ Render with proper path
    return render(request, 'accommodation/my_bookings.html', {'bookings': user_bookings})