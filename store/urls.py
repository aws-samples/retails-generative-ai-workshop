from django.urls import path
from . import views

urlpatterns = [
    path('', views.store, name='store'),
    path('category/<slug:category_slug>/', views.store, name='products_by_category'),
    path('category/<slug:category_slug>/<slug:product_slug>/', views.product_detail, name='product_detail'), 
    path('search/', views.search, name='search'),
    path('submit_review/<int:product_id>/', views.submit_review, name='submit_review'),
    path('generate_description/<int:product_id>/', views.generate_description, name='generate_description'),
    path('save_product_description/<int:product_id>/', views.save_product_description, name='save_product_description'),
    path('design_studio/<int:product_id>/', views.design_studio, name='design_studio'),
    path('create_response/<int:product_id>/<int:review_id>/', views.create_response, name='create_response'),
    path('save_review_response/<int:product_id>/<int:review_id>/', views.save_review_response, name='save_review_response'),
    path('generate_summary/<int:product_id>/', views.generate_summary, name='generate_summary'),
    path('save_summary/<int:product_id>/', views.save_summary, name='save_summary'),
    
    #### REGISTER GENAI URLS BELOW ####
    path('generate_product_description/<int:product_id>/', views.generate_product_description, name='generate_product_description'),
    path('create_review_response/<int:product_id>/<int:review_id>/', views.create_review_response, name='create_review_response'),
    path('create_design_ideas/<int:product_id>', views.create_design_ideas, name='create_design_ideas'),
    path('generate_review_summary/<int:product_id>/', views.generate_review_summary, name='generate_review_summary'),
    path('ask_question/', views.ask_question, name='ask_question'),
    path('vector_search/', views.vector_search, name='vector_search'),
]