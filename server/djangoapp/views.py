from django.shortcuts import render
from django.http import HttpResponseRedirect, HttpResponse
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib import messages
from datetime import datetime
import logging
import json
# from .models import related models
from .models import CarModel
# from .restapis import related methods
from .restapis import get_dealers_from_cf, get_dealer_by_id_from_cf, get_dealer_reviews_from_cf, post_request

# Get an instance of a logger
logger = logging.getLogger(__name__)


# Create your views here.


# Create an `about` view to render a static about page
def about(request):
    context = {}
    if request.method == 'GET':
        return render(request, 'djangoapp/about.html', context)


# Create a `contact` view to return a static contact page
def contact(request):
    context = {}
    if request.method == 'GET':
        return render(request, 'djangoapp/contact.html', context)

# Create a `login_request` view to handle sign in request
def login_request(request):
    context = {}
    if request.method == "POST":
        username = request.POST['username']
        password = request.POST['psw']
        user = authenticate(username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('djangoapp:index')
        else:
            context['message'] = "Invalid username or password."
            return render(request, 'djangoapp/user_login.html', context)
    else:
        return render(request, 'djangoapp/user_login.html', context)

# Create a `logout_request` view to handle sign out request
def logout_request(request):
    logout(request)
    return redirect('djangoapp:index')

# Create a `registration_request` view to handle sign up request
def registration_request(request):
    context = {}
    if request.method == 'GET':
        return render(request, 'djangoapp/user_registration.html', context)
    elif request.method == 'POST':
        # Check if user exists
        username = request.POST['username']
        password = request.POST['psw']
        first_name = request.POST['firstname']
        last_name = request.POST['lastname']
        user_exist = False
        try:
            User.objects.get(username=username)
            user_exist = True
        except:
            logger.error("New user")
        if not user_exist:
            user = User.objects.create_user(username=username, first_name=first_name, 
                                            last_name=last_name,
                                            password=password)
            login(request, user)
            return redirect("djangoapp:index")
        else:
            context['message'] = "User already exists."
            return render(request, 'djangoapp/user_registration.html', context)

# Update the `get_dealerships` view to render the index page with a list of dealerships
def get_dealerships(request):
    context = {}
    url = "https://eu-de.functions.appdomain.cloud/api/v1/web/e99abf15-8841-4599-9c48-d05a8fe571c5/dealership-package/get-dealership"
    # if request.method == "GET":
    #     return render(request, 'djangoapp/index.html', context)
    # Get dealers from the URL
    context = {"dealerships": get_dealers_from_cf(url)}
    # Concat all dealer's short name
    # Return a list of dealer short name
    return render(request, 'djangoapp/index.html', context)
    # if request.method == "GET":
    #     url = "https://eu-de.functions.appdomain.cloud/api/v1/web/e99abf15-8841-4599-9c48-d05a8fe571c5/dealership-package/get-dealership"
    #     # Get dealers from the URL
    #     dealerships = get_dealers_from_cf(url)
    #     # Concat all dealer's short name
    #     dealer_names = ' '.join([dealer.short_name for dealer in dealerships])
    #     # Return a list of dealer short name
    #     return HttpResponse(dealer_names)


# Create a `get_dealer_details` view to render the reviews of a dealer
# def get_dealer_details(request, dealer_id):
def get_dealer_details(request, dealer_id):
    context = {}
    if request.method == "GET":
        url = 'https://eu-de.functions.appdomain.cloud/api/v1/web/e99abf15-8841-4599-9c48-d05a8fe571c5/dealership-package/get-review'
        context = {"reviews":  get_dealer_reviews_from_cf(url, dealer_id)}
        return render(request, 'djangoapp/dealer_details.html', context)

# Create a `add_review` view to submit a review
# def add_review(request, dealer_id):
# ...
def add_review(request, dealer_id):
    # User must be logged in before posting a review
    if request.user.is_authenticated:
        # GET request renders the page with the form for filling out a review
        if request.method == "GET":
            url = f"https://eu-de.functions.appdomain.cloud/api/v1/web/e99abf15-8841-4599-9c48-d05a8fe571c5/dealership-package/get-dealership?dealerId={dealer_id}"
            # Get dealer details from the API
            context = {
                "cars": CarModel.objects.all(),
                "dealer": get_dealer_by_id_from_cf(url, dealer_id=dealer_id),
            }
            return render(request, 'djangoapp/add_review.html', context)

        # POST request posts the content in the review submission form to the Cloudant DB using the post_review Cloud Function
        if request.method == "POST":
            form = request.POST
            review = dict()
            review["name"] = f"{request.user.first_name} {request.user.last_name}"
            review["dealership"] = dealer_id
            review["review"] = form["content"]
            review["purchase"] = form.get("purchasecheck")
            if review["purchase"]:
                review["purchase_date"] = datetime.strptime(form.get("purchasedate"), "%m/%d/%Y").isoformat()
            car = CarModel.objects.get(pk=form["car"])
            review["car_make"] = car.car_make.name
            review["car_model"] = car.name
            review["car_year"] = car.year
            
            # If the user bought the car, get the purchase date
            if form.get("purchasecheck"):
                review["purchase_date"] = datetime.strptime(form.get("purchasedate"), "%m/%d/%Y").isoformat()
            else: 
                review["purchase_date"] = None

            url = "https://eu-de.functions.cloud.ibm.com/api/v1/namespaces/e99abf15-8841-4599-9c48-d05a8fe571c5/actions/dealership-package/get-review"  # API Cloud Function route
            json_payload = {"review": review}  # Create a JSON payload that contains the review data

            # Performing a POST request with the review
            result = post_request(url, json_payload, dealerId=dealer_id)
            if int(result.status_code) == 200:
                print("Review posted successfully.")

            # After posting the review the user is redirected back to the dealer details page
            return redirect("djangoapp:dealer_details", dealer_id=dealer_id)

    else:
        # If user isn't logged in, redirect to login page
        print("User must be authenticated before posting a review. Please log in.")
        return redirect("/djangoapp/login")
