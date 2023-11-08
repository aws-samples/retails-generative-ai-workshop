from django.shortcuts import render, redirect
from .models import Product, ReviewRating, ProductGallery, Variation
from .forms import ReviewForm
from category.models import Category
from django.shortcuts import get_object_or_404
from carts.models import CartItem
from carts.views import _cart_id
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.db.models import Q
from django.contrib import messages
from orders.models import OrderProduct
import os
from utils import bedrock, print_ww
from langchain.llms.bedrock import Bedrock
from langchain.embeddings import BedrockEmbeddings
from langchain import PromptTemplate
import warnings
from PIL import Image
import base64
import io
import json
import random
from decouple import config
import boto3
import string
import numpy as np
import requests
import psycopg2
from pgvector.psycopg2 import register_vector

# Initialize Bedrock client 
boto3_bedrock = bedrock.get_bedrock_client(assumed_role=os.environ.get("BEDROCK_ASSUME_ROLE", None), region=config("AWS_DEFAULT_REGION"))

# Initialize S3 client
s3 = boto3.client('s3', region_name=config("AWS_DEFAULT_REGION"))

# Initialize secrets manager
secrets = boto3.client('secretsmanager', region_name=config("AWS_DEFAULT_REGION"))

# Create your views here.

####################### START SECTION - OTHER WEB APPLICATION FEATURES ##########################

## This section contains functions that will be used for other functionalities of our retail web application.
## For example, submitting user review or displaying products in catalog.

## This section can be safely ignored
## Please don't modify anything in this section

def store(request, category_slug=None):
    categories = None
    products = None

    if category_slug != None:
       categories = get_object_or_404(Category, slug=category_slug)
       products = Product.objects.filter(category=categories, is_available=True).order_by('category')
       paginator = Paginator(products, 6)
       page = request.GET.get('page')
       paged_products = paginator.get_page(page)
       product_count = products.count()
    else:
        products = Product.objects.all().filter(is_available=True).order_by('category')
        paginator = Paginator(products, 6)
        page = request.GET.get('page')
        paged_products = paginator.get_page(page)
        product_count = products.count()

    context = {
        'products': paged_products,
        'product_count': product_count,
    }
    return render(request, 'store/store.html', context)

def product_detail(request, category_slug, product_slug):
    request.session['product_description_flag'] = False
    request.session['product_details'] = None
    request.session['draft_flag'] = False
    request.session['summary_flag'] = False
    request.session['image_flag'] = False
    request.session['change_prompt'] = None
    request.session['negative_prompt'] = None
    request.session.modified = True

    try:
        single_product = Product.objects.get(category__slug=category_slug, slug=product_slug)
        in_cart = CartItem.objects.filter(cart__cart_id=_cart_id(request), product=single_product).exists()
    except Exception as e:
        raise e

    if request.user.is_authenticated:
        try:
            orderproduct = OrderProduct.objects.filter(user=request.user, product_id=single_product.id).exists()
        except OrderProduct.DoesNotExist:
            orderproduct = None
    else:
        orderproduct = None

    # Get reviews
    reviews = ReviewRating.objects.filter(product_id=single_product.id, status=True)

    # Get product gallery
    product_gallery = ProductGallery.objects.filter(product_id=single_product.id)

    context = {
        'single_product': single_product,
        'in_cart'       : in_cart,
        'orderproduct': orderproduct,
        'reviews': reviews,
        'product_gallery': product_gallery,
    }
    #print("user ->" +reviews[0].user.full_name())
    return render(request, 'store/product_detail.html', context)

def search(request):
    if 'keyword' in request.GET:
        keyword = request.GET['keyword']
        if keyword:
            products = Product.objects.order_by('-created_date').filter(Q(description__icontains=keyword) | Q(product_name__icontains=keyword))
            product_count = products.count()
    context = {
        'products': products,
        'product_count': product_count,
    }
    return render(request, 'store/store.html', context)

def submit_review(request, product_id):
    url = request.META.get('HTTP_REFERER')
    first_name=request.POST.get('first_name')
    last_name=request.POST.get('last_name')
    if request.method == 'POST':
        try:
            reviews = ReviewRating.objects.get(first_name=first_name, last_name=last_name, product__id=product_id)
            form = ReviewForm(request.POST, instance=reviews)
            form.save()
            messages.success(request, 'Thank you! Your review has been updated.')
            return redirect(url)
        except ReviewRating.DoesNotExist:
            form = ReviewForm(request.POST)
            if form.is_valid():
                data = ReviewRating()
                data.subject = form.cleaned_data['subject']
                data.rating = form.cleaned_data['rating']
                data.review = form.cleaned_data['review']
                data.ip = request.META.get('REMOTE_ADDR')
                data.product_id = product_id
                #data.user_id = request.user.id
                data.first_name = first_name
                data.last_name = last_name
                data.save()
                messages.success(request, 'Thank you! Your review has been submitted.')
                return redirect(url)

####################### END SECTION - OTHER WEB APPLICATION FEATURES ##########################

####################### START SECTION - HANDLER FUNCTIONS GENAI FEATURES ##########################

## Functions in this section will be used to: 

# 1. Render HTML pages needed for the GenAI features we are going to implement
# 2. Save LLM response to web application database
# 3. Any andler functions used for manipulating input fed to the LLM 

## This section can be safely ignored
## Please don't modify anything in this section

#### HANDLER FUNCTIONS FOR GENERATING PRODUCT DESCRIPTION FEATURE ####

# This function is used to just render HTML page for generate product description functionality
def generate_description(request, product_id):
   try:
        # get product from product ID 
        single_product = Product.objects.get(id=product_id)

   except Exception as e:
        raise e
   
   # pass product object to context (to be used in generate_description.html)
   context = {
        'single_product': single_product,
    }
   
   # render HTML page generate_description.html
   return render(request, 'store/generate_description.html', context)

#This function is used for saving product description to database
def save_product_description(request, product_id):
    try:
        single_product = Product.objects.get(id=product_id)

        # If user input is to save description
        if 'save_description' in request.POST:
            single_product.description = request.POST.get('generated_description')
            single_product.save()
            success_message = "The product description for " + single_product.product_name + " has been updated successfully. "
            messages.success(request, success_message)
            return redirect('product_detail', single_product.category.slug, single_product.slug)
        # If user input is to regenerate
        elif 'regenerate' in request.POST:
            request.session['product_description_flag'] = False
            request.session.modified = True
            return redirect('generate_description', single_product.id)
        else:
            # do nothing
            pass
    except Exception as e:
        raise e

#### HANDLER FUNCTIONS FOR DRAFTING RESPONSE TO CUSTOMER REVIEW FEATURE ####

# This function is used to just render HTML page for create response to customer review functionality
def create_response(request, product_id, review_id):
    try:
        # get product from product ID
        single_product = Product.objects.get(id=product_id)
        # get single customer review using product ID, review ID
        review = ReviewRating.objects.get(product=single_product, id=review_id)

    except Exception as e:
            raise e
    
    # pass objects to context (to be used in create_response.html)
    context = {
            'single_product': single_product,
            'review': review,
        }
    # render HTML page create_response.html
    return render(request, 'store/create_response.html', context)

# This function is used for saving customer review response to database
def save_review_response(request, product_id, review_id):
    try:
        # get single product review using product ID and review ID 
        request.session['draft_flag'] = False
        single_product = Product.objects.get(id=product_id)
        review = ReviewRating.objects.get(product=single_product, id=review_id)

        # If user input is to save response
        if 'save_response' in request.POST:
            review.generated_response = request.POST.get('generated_response')
            review.prompt = request.session.get('draft_prompt')
            review.save()
            success_message = "The response for the review of " + single_product.product_name + " has been updated successfully. "
            messages.success(request, success_message)
            return redirect('product_detail', single_product.category.slug, single_product.slug)
        
        # If user input is to regenerate review response
        elif 'regenerate' in request.POST:
            request.session.modified = True
            return redirect('create_response', single_product.id, review.id)
        else:
            # do nothing
            pass
    except Exception as e:
        raise e

#### HANDLER FUNCTIONS FOR SUMMARIZING CUSTOMER REVIEWS FEATURE ####

# This function is used to just render HTML page for summarize customer reviews functionality
def generate_summary(request, product_id): 
    try:
        # get product from product ID
        single_product = Product.objects.get(id=product_id)
        # get all customer reviews for this product
        product_reviews = ReviewRating.objects.filter(product=single_product, status=True)

    except Exception as e:
            raise e
    
    # pass objects to context (to be used in generate_summary.html)
    context = {
            'single_product': single_product,
            'reviews': product_reviews,
        }
    
    # render HTML page generate_summary.html
    return render(request, 'store/generate_summary.html', context)

# This function is used for saving summarized customer reviews to database
def save_summary(request, product_id):
    try:
        # get single product review using product ID and review ID 
        single_product = Product.objects.get(id=product_id)
        request.session['summary_flag'] = False

        # If user input is to save review summary
        if 'save_summary' in request.POST:
            single_product.review_summary = request.session['generated_summary']
            single_product.save()
            success_message = "The summary for the review of " + single_product.product_name + " has been updated successfully. "
            messages.success(request, success_message)
            return redirect('product_detail', single_product.category.slug, single_product.slug)
        # If user input is to regenerate review summary
        elif 'regenerate' in request.POST:
            request.session.modified = True
            return redirect('generate_summary', single_product.id)
        else:
            # do nothing
            pass
    except Exception as e:
        raise e

#### HANDLER FUNCTIONS FOR CREATING NEW DESIGN IDEAS FEATURE ####

# This function is used to just render the HTML page studio.html
def design_studio(request, product_id):
    single_product = Product.objects.get(id=product_id)
    context = {
        'single_product': single_product,
    }
    return render(request, 'store/studio.html', context)

# Handy function to convert an image to base64 string
# Stabile Diffusion LLM expects the input image to be in base64 string format
def image_to_base64(img) -> str:
    """Convert a PIL Image or local image file path to a base64 string for Amazon Bedrock"""
    if isinstance(img, str):
        if os.path.isfile(img):
            with open(img, "rb") as f:
                return base64.b64encode(f.read()).decode("utf-8")
        else:
            raise FileNotFoundError(f"File {img} does not exist")
    elif isinstance(img, Image.Image):
        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        return base64.b64encode(buffer.getvalue()).decode("utf-8")
    else:
        raise ValueError(f"Expected str (filename) or PIL Image. Got {type(img)}")

#### HANDLER FUNCTIONS FOR QUESTION ANSWERING FEATURE ####

# This function is used for extracting string within a tag. For example, get string embedded within <query></query>
def extract_strings_recursive(test_str, tag):
    # finding the index of the first occurrence of the opening tag
    start_idx = test_str.find("<" + tag + ">")
 
    # base case
    if start_idx == -1:
        return []
 
    # extracting the string between the opening and closing tags
    end_idx = test_str.find("</" + tag + ">", start_idx)
    res = [test_str[start_idx+len(tag)+2:end_idx]]
 
    # recursive call to extract strings after the current tag
    res += extract_strings_recursive(test_str[end_idx+len(tag)+3:], tag)
 
    return res

####################### END SECTION - HANDLER FUNCTIONS GENAI FEATURES ##########################

####################### END SECTION - HANDLER FUNCTIONS GENAI FEATURES ##########################

####################### START SECTION - IMPLEMENT GENAI FEATURES FOR WORKSHOP ##########################

#### This is the only section where you will add functions needed for implementing GenAI features into your retail application
#### Please don't edit any sections other than this one. 

#### FEATURE 1 - GENERATE PRODUCT DESCRIPTION ####



#### FEATURE 2 - DRAFTING RESPONSE TO CUSTOMER REVIEWS ####



#### FEATURE 3 - CREATE NEW DESIGN IDEAS FROM PRODUCT ####



#### FEATURE 4 - SUMMARIZE CUSTOMER REVIEWS FOR A PRODUCT ####



#### FEATURE 5 - QUESTION ANSWERING WITH SQL GENERATION ####



#### FEATURE 6 - VECTOR SEARCH ####



####################### END SECTION - IMPLEMENT GENAI FEATURES FOR WORKSHOP ##########################