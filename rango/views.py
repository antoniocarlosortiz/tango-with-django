from django.shortcuts import render
from django.http import HttpResponse
from rango.models import Category, Page, UserProfile
from rango.forms import CategoryForm, PageForm, UserForm, UserProfileForm
from django.contrib.auth import authenticate, login
from django.http import HttpResponseRedirect, HttpResponse
from django.contrib.auth.decorators import login_required
from datetime import datetime
from rango.bing_search import run_query
from django.shortcuts import redirect
from django.contrib.auth.models import User

def track_url(request):
    context_dict = {}

    if request.method == "GET":
        if 'page_id' in request.GET:
            page_id = request.GET['page_id']
            print type(page_id)

            page = Page.objects.get(pk=int(page_id))
            if page:
                page.views = page.views + 1
                page.save()

                return redirect(page.url)

    return render(request, 'rango/index.html', context_dict)

#   save session info in the backend by using the session id cookie of the user which is stored
# in the client side.
def index(request):
    category_list = Category.objects.all()
    page_list = Page.objects.order_by('-views')[:5]

    context_dict = {'categories': category_list, 'pages': page_list}

    visits = request.session.get('visits')
    if not visits:
        visits = 1

    reset_last_visit_time = False

    last_visit = request.session.get('last_visit')
    if last_visit:
        last_visit_time = datetime.strptime(last_visit[:-7], "%Y-%m-%d %H:%M:%S")

        if (datetime.now() - last_visit_time).seconds > 0:
            # ...reassign the value of the cookie to +1 of what it was before...
            visits = visits + 1
            # ...and update the last visit cookie, too.
            reset_last_visit_time = True

    else:
        # Cookie last_visit doesn't exist, so create it to the current date/time.
        reset_last_visit_time = True

    if reset_last_visit_time:
        request.session['last_visit'] = str(datetime.now())
        request.session['visits'] = visits

    context_dict['visits'] = visits

    response = render(request, 'rango/index.html', context_dict)

    return response


def about(request):
    context_dict = {}

    if request.session.get('visits'):
        count = request.session.get('visits')
    else:
        count = 0

    context_dict['visits'] = count

    return render(request, 'rango/about.html', context_dict)


def category(request, category_name_slug):
    context_dict = {}

    if request.method == 'POST':
        query = request.POST['query'].strip()
        if query:
            category = Category.objects.filter(slug=query)
            context_dict['result_list'] = category

            return render(request, 'rango/category.html', context_dict)

    try:
        category = Category.objects.get(slug=category_name_slug)
        context_dict['category_name'] = category.name

        pages = Page.objects.filter(category=category)

        context_dict['pages'] = pages
        context_dict['category'] = category

    except Category.DoesNotExist:
        pass

    return render(request, 'rango/category.html', context_dict)


def search(request):

    result_list = []

    if request.method == 'POST':
        query = request.POST['query'].strip()

        if query:
            # Run our Bing function to get the results list!
            result_list = run_query(query)

    return render(request, 'rango/search.html', {'result_list': result_list})


@login_required
def add_category(request):
    if request.method == 'POST':
        form = CategoryForm(request.POST)

        if form.is_valid():
            form.save(commit=True)

            return index(request)
        else:
            print form.errors
    else:
        form = CategoryForm()

    return render(request, 'rango/add_category.html', {'form': form})

@login_required
def add_page(request, category_name_slug):

    try:
        cat = Category.objects.get(slug=category_name_slug)
    except Category.DoesNotExist:
        cat = None

    if request.method == "POST":
        form = PageForm(request.POST)
        if form.is_valid():
            if cat:
                page = form.save(commit=False)
                page.category = cat
                page.views = 0
                page.save()

                return category(request, category_name_slug)
        else:
            print form.errors

    else:
        form = PageForm()

    context_dict = {'form': form, 'category': cat}

    return render(request, 'rango/add_page.html', context_dict)

'''
def register(request):
    # A boolean value for telling the template whether the registration was successful.
    # Set to False initially. Code changes value to True when registration succeeds.
    registered = False

    # If it's a HTTP POST, we're interested in processing form data.
    if request.method == 'POST':
        # Attempt to grab information from the raw form information.
        # Note that we make use of both UserForm and UserProfileForm.
        user_form = UserForm(data=request.POST)
        profile_form = UserProfileForm(data=request.POST)

        #If the two forms are valid...
        if user_form.is_valid() and profile_form.is_valid():
            #Save the user's form data to the database.
            user = user_form.save()

            #Now we hash the password witht he set_password method.
            #Once hashed, wecan update the user object.
            user.set_password(user.password)
            user.save()

            # Now sort out the UserProfile instance.
            # Since we need to set te user attribute ourselves, we set
            # This delays saving the model until we're ready to avoid integrity problems.
            profile = profile_form.save(commit=False)
            profile.user = user

            # Did the user provide a profile picture picture?
            # If so we need to get it from the input form and put it in the UserProfile model.
            if 'picture' in request.FILES:
                profile.picture = request.FILES['picture']

            print request.FILES
            # Now we save the UserProfile model instance.
            profile.save()

            # Update our variable to tell the template registration was successful.
            registered = True

        # Invalid form or forms - mistakes or something else?
        # Print problems to the terminal.
        # They'll also be shown to the user.
        else:
            print user_form.errors, profile_form.errors

    # Not a HTTP POST, so we render our form using two ModelForm instances.
    # These forms will be blank, ready for user input.
    else:
        user_form = UserForm()
        profile_form = UserProfileForm()

    # Render the template depending on the context.
    return render(request,
            'rango/register.html',
            {'user_form': user_form, 'profile_form': profile_form, 'registered': registered})


def user_login(request):

    #If the request is an HTTP POST, try to pull out the relevant information.
    if request.method == "POST":
        #Gather the username and password provided by the user.
        #This information is obtained from the login form.
            #We use request.POST.get('<variable>') as opposed to request.POST['<variable>']
            #because the request.POST,get('<variable>') returns None, if the value does not
            #exist, while request.POST ['<variable>'] will raise key error Exception.
        username = request.POST.get('username')
        password = request.POST.get('password')

        # Use Django's machinery to attempt to see if the username/password
        # combination is valid - a User object is returned if it is.
        user = authenticate(username=username, password=password)

        # If we have a User object, the details are correct.
        # If None (Python's way of representing the absence of a value), no user
        # with matching credentials was found.
        if user:
            # Is the account active? It could have been disabled.
            if user.is_active:
                # If the account is valid and acive, we can log the user in.
                login(request, user)
                return HttpResponseRedirect('/rango/')
            else:
                # an inactive account was used - no logging in!
                return HttpResponse("You're rango account is disabled")

        else:
            # Bad login details were provided. So we can't log the user in.
            error_message = 'Invalid login details: {0}, {1}'.format(username, password)
            return render(request, 'rango/login.html', {'error_message':error_message})

        # The request is not an HTTP POST, so display the login form.
        # This scenario would most likely be an HTTP GET
    else:
        # No context variable to pass to the template system, hence the blank dictionary
        # object.
        return render(request, 'rango/login.html', {})


from django.contrib.auth import logout

@login_required
def user_logout(request):
    logout(request)

    return HttpResponseRedirect('/rango/')
'''


@login_required
def restricted(request):
    return render(request, 'rango/restricted.html', {})

def search(request):

    result_list = []

    if request.method == 'POST':
        query = request.POST['query'].strip()

        if query:
            # Run our Bing function to get the results list!
            result_list = run_query(query)

    return render(request, 'rango/search.html', {'result_list': result_list})


@login_required
def register_profile(request):
    args = {}
    user = request.user

    try:
        user_profile = UserProfile.objects.get(user=user)
        args['profile_form'] = UserProfileForm(instance=user_profile)
    except Exception as e:
        print repr(e)
        args['profile_form'] = UserProfileForm()

    if request.method == 'POST':
        try:
            user_profile = UserProfile.objects.get(user=user)
            profile_form = UserProfileForm(request.POST, request.FILES, instance=user_profile)
        except Exception as e:
            print repr(e)
            profile_form = UserProfileForm(request.POST, request.FILES)

        if profile_form.is_valid():
            profile = profile_form.save(commit=False)
            profile.user = user
            profile.save()
            return HttpResponseRedirect('/rango/')

    return render(request, 'rango/profile_registration.html', args)


@login_required
def list_users(request):
    args = {}
    args['current_user'] = request.user
    users = User.objects.all()
    args['users'] = users


    return render(request, 'rango/list-users.html', args)


@login_required
def view_user(request, user_pk):
    args = {}

    user = User.objects.get(pk=user_pk)
    args['user'] = user
    try:
        user_profile = UserProfile.objects.get(user=user)
        args['user_profile'] = user_profile
    except Exception as e:
        print repr(e)

    return render(request, 'rango/view-user.html', args)