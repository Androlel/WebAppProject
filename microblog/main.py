import datetime
import dateutil.tz
from . import db
from flask import Blueprint, render_template, redirect, request, url_for, abort
from . import model
import flask_login
from flask_login import current_user

bp = Blueprint("main", __name__)

# what is index doing, lab didnt say anything ab updating like it did for message and user
@bp.route("/")
@flask_login.login_required
def index():
    # modified to not include any responses on main feed
   # query = db.select(model.Message).where(model.Message.response_to==None).order_by(model.Message.timestamp.desc()).limit(10)
   # print(query)
    followers = db.aliased(model.User)
    query = (
        db.select(model.Message)
        .join(model.User)
        .join(followers, model.User.followers)
        .where(followers.id == flask_login.current_user.id)
        .where(model.Message.response_to == None)
        .order_by(model.Message.timestamp.desc())
        .limit(10)
    )
  
    # runs query we just created and gets results using scalars.all, 
    # converts one row to one Message object since query will return a row 
    # use scalar().all() whenever need a list of results 
    posts = db.session.execute(query).scalars().all()
  
    return render_template("main/index.html", posts=posts)

@bp.route("/user/<int:user_id>")
@flask_login.login_required
def user(user_id):
   # goes to table w/ users and looks for id of user, get is int type
    user = db.session.get(model.User, user_id)
    if not user:
        abort(404, "User_id {} doesn't exist.".format(user_id))

    query = db.select(model.Message).where((model.Message.user == user) and (model.Message.response_to==None)).order_by(model.Message.timestamp.desc())
    posts = db.session.execute(query).scalars().all()

    if current_user.id == user_id:# looking at my profile 
        follow_button = "none"
    elif flask_login.current_user not in user.followers:# is the current_user the user being looked at or who is logged in
        follow_button = "follow"
    elif flask_login.current_user in user.followers:
        follow_button = "unfollow"
    else:
        abort(404, "couldn't determine user relation to current_user")

        
    # blue is name in template, can pass thru anything, white is variable that gives it value
   # not sure if follow_button implemented correct 
    return render_template("main/display_profile_template.html", user=user, posts=posts, follow_button=follow_button)

@bp.route("/message/<int:message_id>")
@flask_login.login_required
# called post in example
def message(message_id):
   # goes to table w/ messages and looks for message id 
    message = db.session.get(model.Message, message_id)
    if not message:
        abort(404, "Post id {} doesn't exist.".format(message_id))
    
   # gets message responses 
    query =  db.select(model.Message).where(model.Message.response_to_id == message_id).order_by(model.Message.timestamp.desc())
    responses = db.session.execute(query).scalars()

    if model.Message.response_to_id == 0:
        abort(404, "Message is a response")
    
    # could be unnecessary since will run if initial message doesnt exist but we already checked
   # message = db.get_or_404(model.Message, message_id)

   # changed responses=[] to =responses 
    return render_template("main/message.html", post=message, posts=responses)

# get request by default so dont need method post, depending on post/get request 
# will run one of the two following functions, even with same path
@bp.route("/new_post") 
@flask_login.login_required
def new_post_form():
    return render_template("main/new_post.html")
# I added, I think I need it to be able to access the response text

@bp.route("/new_post") 
@flask_login.login_required
def new_response_form():
    return render_template("main/message.html")


# do I need methods=[post] part: yes
@bp.route("/new_post", methods=["POST"]) 
@flask_login.login_required
def new_post():

    # gets the post that the response is responding to
    message_id = request.form.get("response_to")
    caption = request.form.get("caption")
    if message_id != None:
        # therefore response message
        #print("THIS IS A RESPONSE MESSAGE")
        # gets the original post 
        query = db.select(model.Message).where(model.Message.id == message_id)
        #message = db.session.execute(query).scalar_one_or_none()
        message = db.get_or_404(model.Message, message_id) # shortcut 

       # print("model.Message.text: ", message.text)

        new_post = model.Message(
            text=caption,
            user=current_user,
            timestamp=datetime.datetime.now(dateutil.tz.tzlocal()),
            response_to=message,
        )
       # print("response_message.text: ", new_post.text)
    
    else:
        # not response message, first message
        # flask remembers current_user 
        new_post = model.Message(
            text=caption,
            user=current_user, # user_id=current_user.id if wanted to pass via id
            timestamp=datetime.datetime.now(dateutil.tz.tzlocal()),
            # response_to is default set to nothing
        )
    db.session.add(new_post)
    db.session.commit()
    # test print 
   # print(url_for("main.message", message_id=new_post.id))

   # important! look at message and how it connects message_id 
    return redirect(url_for("main.message", message_id=new_post.id))


# untested
@bp.route("/follow/<int:user_id>", methods=["POST"])
@flask_login.login_required
def follow(user_id):
    query = db.select(model.User).where(model.User.id == user_id)
    #user = db.session.execute(query).scalar_one_or_none()

   # gets user, otherwise returns 404 not found error 
    user = db.get_or_404(model.User, user_id) # shortcut 

    # checks if same user
    # print("Current_user: ", current_user)
    # print("user_id: ", user_id)
    # print("user.id: ", user.id)
    if user_id == current_user:# user being looked at is the user logged in 
       abort(403, "Forbidden") 

   # checks if current user is already following 
    if flask_login.current_user in user.followers:
        abort(404, "User already follows this account")
   # also checks if user already follows but other way around 
   # user in flask_login.current_user.following

    user.followers.append(flask_login.current_user)
    db.session.commit()
    # print("HERE IS user.followers: ", user.followers ," of ", user.name)# seems to print who current_user is following 
    # print("HERE IS user.following: ", user.following ," of ", user.name)# seems to print current_user is followed by
   
  # not sure if right (lab 6 exercise 5) 
    return render_template("main/display_profile_template.html", user=user)
   # return redirect(url_for("main/display_profile_template.html"), user = user)

# modeled after follow function above, untested
@bp.route("/unfollow/<int:user_id>", methods=["POST"])
@flask_login.login_required
def unfollow(user_id):
    query = db.select(model.User).where(model.User.id == user_id)
    #user = db.session.execute(query).scalar_one_or_none()

   # gets user, otherwise returns 404 not found error 
    user = db.get_or_404(model.User, user_id) # shortcut 

    # checks if same user
    if user_id == current_user:
       abort(403, "Forbidden") 

   # checks if current user is following 
    if flask_login.current_user not in user.followers:
        abort(404, "User doesn't follow this account")


    user.followers.remove(flask_login.current_user)
    db.session.commit()
    # print("HERE IS user.followers: ", user.followers ," of ", user.name)# seems to print who current_user is following 
    # print("HERE IS user.following: ", user.following ," of ", user.name)# seems to print current_user is followed by
   
  # not sure if right (lab 6 exercise 5) 
    return render_template("main/display_profile_template.html", user=user)
   


