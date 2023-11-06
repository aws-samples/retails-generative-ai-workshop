from .models import Category

def menu_links(request):
    links = Category.objects.all().order_by('category_name')
    return dict(links=links)