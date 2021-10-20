from django.shortcuts import render
from django.http import HttpResponse
from django.contrib.auth.models import User
from .models import Pending_Requests
from .models import Done_Requests

import smtplib
from email.message import EmailMessage

review_request_mail_msg = "Hi {0}!\n\nThis automated message was sent to you because you have a new review request from {1}\n\nDetails -\n\nRequest sent at: {2} UTC\nDate: {3}\nComments for the reviewer: \n{4}\n\nHave a nice day!\nTeam d.bug"




def welcome_view(request, *args, **keywordargs):
    return render(request, 'welcome.html', {})


def home_view(request, *args, **keywordargs):
    return render(request, 'home.html', {})

def pending_view(request, *args, **keywordargs):
    user = request.user.username
    code_snippet = [e.code for e in Pending_Requests.objects.all()
                    if e.req_to == user]

    req_from = [e.req_from for e in Pending_Requests.objects.all()
                if e.req_to == user]

    req_id = [e.id for e in Pending_Requests.objects.all()
              if e.req_to == user]

    comments = [e.comments for e in Pending_Requests.objects.all()
                if e.req_to == user]
    data = zip(code_snippet, req_from, comments, req_id)

    context = {"data": tuple(data)}
    return render(request, 'pending.html', context)


def request_new_view(request, *args, **keywordargs):
    username_list = [e.username for e in User.objects.all()]
    context = { "username_list": username_list}

    return render(request, 'review_request.html', context)


def reviewed_view(request, *args, **keywordargs):
    user = request.user.username
    code_snippets = [e.code for e in Done_Requests.objects.all()
                     if e.req_to == user]

    req_from = [e.req_from for e in Done_Requests.objects.all()
                if e.req_to == user]

    req_id = [e.id for e in Done_Requests.objects.all()
              if e.req_to == user]

    comments = [e.comments for e in Done_Requests.objects.all()
                if e.req_to == user]

    reviews = [e.reviews_added for e in Done_Requests.objects.all()
               if e.req_to == user]

    data = zip(code_snippets, req_from, comments, req_id, reviews)

    context = {"data": tuple(data)}
    return render(request, 'reviewed.html', context)


def review(request, *args, **keywordargs):
    context = {
        'rid': request.POST.get('req_id'),
        'cs': request.POST.get('code_snippet'),
        'rf': request.POST.get('req_from'),
        'comment': request.POST.get('comment')
    }

    return render(request, 'review_page.html', context)


def team_view(request, *args, **keywordargs):
    return render(request, 'team.html', {})


def about_view(request, *args, **keywordargs):
    return render(request, 'about.html', {})


def contact_view(request, *args, **keywordargs):
    return render(request, 'contact.html', {})


def send_review_request_mail(code, email_id, username_to_req, username_from_req, comment, time):
    to_send = EmailMessage()

    msg = review_request_mail_msg.format(str(username_to_req), str(username_from_req), str(time.split(" ")[1]), str(time.split(" ")[0]), str(comment))

    to_send.set_content(msg)

    to_send['From'] = "reviewalert.dbug@gmail.com"
    to_send['To'] = str(email_id)
    to_send['Subject'] = "d.bug : New Review Request Recieved!"

    s = smtplib.SMTP('smtp.gmail.com', 587)
    s.starttls()
    s.login("email", "password")
    s.send_message(to_send)


def send_review_done_mail(email_id, username_req_from, username_req_to, rev_id, time):
    to_send = EmailMessage()

    msg = "Hi " + str(username_req_from) + "!\n\n" + \
        "This automated message was sent to you because your code has been reviewed by " + username_req_to + "!\n\n" + \
        "Details -\n" + "\nReviewed at: "+ str(time.split(" ")[1]) + \
        " UTC\nDate: " + str(time.split(" ")[0]) + \
        "\nReview ID: " + rev_id + "\n\n" + \
        "Have a nice day!\nTeam d.bug"

    to_send.set_content(msg)

    to_send['From'] = "reviewalert.dbug@gmail.com"
    to_send['To'] = str(email_id)
    to_send['Subject'] = "d.bug : Code Reviewed!"

    s = smtplib.SMTP('smtp.gmail.com', 587)
    s.starttls()
    s.login("email_id", "password")
    s.send_message(to_send)


def send_request(request):
    context = {}
    username_curr = request.user.username
    username = request.POST.get('reviewerInput')
    email_id = ""

    from datetime import datetime
    time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    # get email_id of reviewer
    for i in User.objects.raw('SELECT * FROM auth_user WHERE username = %s', [username]):
        email_id = i.email

    # send email notification to reviewer
    if request.method == 'POST':
        data = {
            'codeInput': request.POST.get('codeInput'),
            'email_id': email_id,
            'username': username,
            'commentInput': request.POST.get('commentInput')
        }

        context = data

        send_review_request_mail(
            data['codeInput'],
            data['email_id'],
            data['username'],
            username_curr,
            data['commentInput'],
            str(time)
        )

    # add new request to pending db
    x = Pending_Requests(
        code=data['codeInput'],
        req_from=request.user.username,
        req_to=data['username'],
        comments=data['commentInput'])
    x.save()

    return render(request, 'mail_sent.html', context)


def review_submitted(request):
    context = {}

    username_req_from = request.POST.get('req_from')
    username_req_to = request.user.username

    email_id_req_from = ""

    # get email_id of reviewee
    for i in User.objects.raw('SELECT * FROM auth_user WHERE username = %s', [username_req_from]):
        email_id_req_from = i.email

    if request.method == 'POST':
        context = {
            'rev_id': request.POST.get('rev_id'),
            'code': request.POST.get('code'),
            'req_from': username_req_from,
            'req_to': username_req_to,
            'email_id_req_from': email_id_req_from,
            'comments': request.POST.get('comments'),
            'review_submitted': request.POST.get('review_text')
        }

        from datetime import datetime
        time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    # send notification (code reviewed)
        send_review_done_mail(
            context['email_id_req_from'],
            context['req_from'],
            context['req_to'],
            context['rev_id'],
            time)

    # remove entry from db
    x = Pending_Requests.objects.get(
        req_from=context['req_from'], comments=context['comments'])
    x.delete()

    # add entry to done db
    x = Done_Requests(
        code=context['code'],
        req_from=context['req_from'],
        req_to=context['req_to'],
        comments=context['comments'],
        reviews_added=context['review_submitted'])
    x.save()

    return render(request, 'review_submitted.html/', context)


def sent_pending_view(request):
    user = request.user.username
    code_snippets = [e.code for e in Pending_Requests.objects.all()
                     if e.req_from == user]

    req_from = [e.req_from for e in Pending_Requests.objects.all()
                if e.req_from == user]
    
    req_to = [e.req_to for e in Pending_Requests.objects.all()
                if e.req_from == user]

    req_id = [e.id for e in Pending_Requests.objects.all()
              if e.req_from == user]

    comments = [e.comments for e in Pending_Requests.objects.all()
                if e.req_from == user]

    data = zip(code_snippets, req_from, req_to, comments, req_id)

    context = {"data": tuple(data)}
    return render(request, 'pending_sent.html', context)


def done_for_me_view(request):
    user = request.user.username
    code_snippets = [e.code for e in Done_Requests.objects.all()
                     if e.req_from == user]

    req_from = [e.req_from for e in Done_Requests.objects.all()
                if e.req_from == user]

    req_id = [e.id for e in Done_Requests.objects.all()
              if e.req_from == user]

    comments = [e.comments for e in Done_Requests.objects.all()
                if e.req_from == user]

    reviews = [e.reviews_added for e in Done_Requests.objects.all()
               if e.req_from == user]

    reviewed_by = [e.req_to for e in Done_Requests.objects.all()
                   if e.req_from == user]

    data = zip(code_snippets, req_from, comments, req_id, reviews, reviewed_by)

    context = {"data": tuple(data)}
    return render(request, 'done_for_me.html', context) 