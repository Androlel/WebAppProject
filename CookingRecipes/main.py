import datetime
import dateutil.tz
from . import db
from flask import Blueprint, render_template, redirect, request, url_for, abort
from . import model
import flask_login
from flask_login import current_user

bp = Blueprint("main", __name__)

   # currently only showing 1 recipe, should be 10  
@bp.route("/")
@flask_login.login_required
def index():
    followers = db.aliased(model.User)
    query = (
        db.select(model.Recipe)
        .join(model.User)
        .join(followers, model.User.followers)
        .where(followers.id == flask_login.current_user.id)
        .where(model.Message.response_to == None)
        .order_by(model.Message.timestamp.desc())
        .limit(1)
    )
    recipe = db.session.execute(query).scalars().all()
  
    return render_template("main/index.html", recipe=recipe)

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
    
    return render_template("main/display_profile_template.html", user=user, posts=posts, follow_button=follow_button)

@bp.route("/message/<int:message_id>")
@flask_login.login_required
# called post in example
def message(message_id):
   # goes to table w/ messages and looks for message id 
    message = db.session.get(model.Message, message_id)
    if not message:
        abort(404, "Post id {} doesn't exist.".format(message_id))
    
    query =  db.select(model.Message).where(model.Message.response_to_id == message_id).order_by(model.Message.timestamp.desc())
    responses = db.session.execute(query).scalars()

    if model.Message.response_to_id == 0:
        abort(404, "Message is a response")

    return render_template("main/message.html", post=message, posts=responses)

@flask_login.login_required
def new_post_form():
    return render_template("main/new_post.html")

@bp.route("/new_post") 
@flask_login.login_required
def new_response_form():
    return render_template("main/message.html")

@bp.route("/new_post", methods=["POST"]) 
@flask_login.login_required
def new_post():
    # gets the post that the response is responding to
    message_id = request.form.get("response_to")
    caption = request.form.get("caption")
    if message_id != None:
        query = db.select(model.Message).where(model.Message.id == message_id)
        message = db.get_or_404(model.Message, message_id) # shortcut 
        new_post = model.Message(
            text=caption,
            user=current_user,
            timestamp=datetime.datetime.now(dateutil.tz.tzlocal()),
            response_to=message,
        )
    else:
        new_post = model.Message(
            text=caption,
            user=current_user, # user_id=current_user.id if wanted to pass via id
            timestamp=datetime.datetime.now(dateutil.tz.tzlocal()),
            # response_to is default set to nothing
        )
    db.session.add(new_post)
    db.session.commit()
    return redirect(url_for("main.message", message_id=new_post.id))


@bp.route("/follow/<int:user_id>", methods=["POST"])
@flask_login.login_required
def follow(user_id):
    query = db.select(model.User).where(model.User.id == user_id)
    user = db.get_or_404(model.User, user_id) # shortcut 

    if user_id == current_user:# user being looked at is the user logged in 
       abort(403, "Forbidden") 

    if flask_login.current_user in user.followers:
        abort(404, "User already follows this account")

    user.followers.append(flask_login.current_user)
    db.session.commit()
    
    return render_template("main/display_profile_template.html", user=user)
   
# modeled after follow function above, untested
@bp.route("/unfollow/<int:user_id>", methods=["POST"])
@flask_login.login_required
def unfollow(user_id):
    query = db.select(model.User).where(model.User.id == user_id)
    user = db.get_or_404(model.User, user_id) # shortcut 

    # checks if same user
    if user_id == current_user:
       abort(403, "Forbidden") 

   # checks if current user is following 
    if flask_login.current_user not in user.followers:
        abort(404, "User doesn't follow this account")


    user.followers.remove(flask_login.current_user)
    db.session.commit()
    
    return render_template("main/display_profile_template.html", user=user)

# controller function for displaying the form that asks for the title, general description, etc. of the new recipe 
@bp.route("/create_recipe", methods=["GET", "POST"])
@flask_login.login_required
def create_recipe_form():
    if request.method == "POST":
        title = request.form.get("title")
        description = request.form.get("description")
        servings = request.form.get("servings")
        time = request.form.get("time")

        # Create a new recipe in the database
        new_recipe = model.Recipe(
            user=current_user,
            title=title,
            description=description,
            servings=servings,
            time=time,
        )
        db.session.add(new_recipe)
        db.session.commit()

        return redirect(url_for('main.edit_recipe', recipe_id=new_recipe.id))

    # For GET requests, render the recipe creation form
    return render_template("recipes/create_recipe_form.html")

# controller function for receiving the data from that form and storing the recipe object
@bp.route("/edit_recipe/<int:recipe_id>", methods=["GET", "POST"])
@flask_login.login_required
def edit_recipe(recipe_id):
    recipe = model.Recipe.query.get_or_404(recipe_id)

    # Handle data submission for updating recipe details if needed
   # NOT SURE IF CORRECT 
    if request.method == "POST":
        title = request.form.get("title")
        description = request.form.get("description")
        servings = request.form.get("servings")
        time = request.form.get("time")

        cooking_steps = request.form.get("cooking_steps")
        ingredients = request.form.getlist("ingredients[]")
        new_ingredients = request.form.getlist("new_ingredients[]")
        quantities = request.form.getlist("quantities[]")
    
        new_recipe = model.Recipe(
            user=current_user,
            title=title,
            description=description,
            servings=servings,
            time=time,
        
        )
        db.session.add(new_recipe)
        db.session.commit()

    return render_template("recipes/edit_recipe.html", recipe=recipe)


# controller function for displaying the current state of the recipe and asking for the next ingredient or step
# represents controller receiving the data about an ingredient and quantity, and storing them as well
# coult be a source of problems^^ 
@bp.route("/edit_recipe/ingredients/<int:recipe_id>", methods=["GET", "POST"])
@flask_login.login_required
def edit_recipe_ingredients(recipe_id):
    recipe = model.Recipe.query.get_or_404(recipe_id)

    if request.method == "POST":
        ingredient_name = request.form.get("ingredient_name")
        quantity = request.form.get("quantity")
        unit = request.form.get("unit")

        # Create a new ingredient and associate it with the recipe
        new_ingredient = model.Ingredient(name=ingredient_name, recipe_id=recipe.id)
        db.session.add(new_ingredient)
        
        quantified_ingredient = model.QuantifiedIngredient(
            recipe=recipe,
            ingredient=new_ingredient,
            quantity=quantity,
            unit=unit,
        )
        db.session.add(quantified_ingredient)
        db.session.commit()

        return redirect(url_for('main.edit_recipe_ingredients', recipe_id=recipe_id))

    return render_template("recipes/edit_recipe_ingredients.html", recipe=recipe)

# controller function for receiving the data about a step, and storing it
@bp.route("/edit_recipe/steps/<int:recipe_id>", methods=["GET", "POST"])
@flask_login.login_required
def edit_recipe_steps(recipe_id):
    recipe = model.Recipe.query.get_or_404(recipe_id)

    if request.method == "POST":
        step_description = request.form.get("step_description")

        # Create a new step and associate it with the recipe
        new_step = model.Step(description=step_description, recipe=recipe)
        db.session.add(new_step)
        db.session.commit()

        return redirect(url_for('main.edit_recipe_steps', recipe_id=recipe_id))

    return render_template("recipes/edit_recipe_steps.html", recipe=recipe)

# controller function for marking the recipe as complete
# routes.py
@bp.route("/complete_recipe/<int:recipe_id>", methods=["POST"])
@flask_login.login_required
def complete_recipe(recipe_id):
    recipe = model.Recipe.query.get_or_404(recipe_id)

    recipe.complete = True
    db.session.commit()

    return redirect(url_for('main.recipe_view', recipe_id=recipe_id))



# i think can delete all below 

# @bp.route("/new_recipe")
# @flask_login.login_required
# def new_recipe_form():
#     return render_template("main/new_recipe.html")


# @bp.route("/new_recipe", methods=["POST"]) 
# @flask_login.login_required
# def new_recipe():

#     if request.method == "POST":

#         title = request.form.get("title")
#         description = request.form.get("description")
#         servings = request.form.get("servings")
#         time = request.form.get("time")

#         cooking_steps = request.form.get("cooking_steps")
#         ingredients = request.form.getlist("ingredients[]")
#         new_ingredients = request.form.getlist("new_ingredients[]")
#         quantities = request.form.getlist("quantities[]")
    
#         new_recipe = model.Recipe(
#             user=current_user,
#             title=title,
#             description=description,
#             servings=servings,
#             time=time,
        
#         )
#         db.session.add(new_recipe)
#         db.session.commit()

#         for i in range(len(ingredients)):
#             ingredient_id = ingredients[i]
#             new_ingredient_name = new_ingredients[i]
#             quantity = quantities[i]

#             if not ingredient_id and new_ingredient_name:
#                 # Create a new ingredient if it doesn't exist
#                 new_ingredient = model.Ingredient(name=new_ingredient_name)
#                 db.session.add(new_ingredient)
#                 db.session.commit()
#                 ingredient_id = new_ingredient.id

#             # Create a relationship between the recipe and the ingredient
#             quantified_ingredient = model.QuantifiedIngredient(
#                 recipe=new_recipe,
#                 ingredient_id=ingredient_id,
#                 quantity=quantity,
#             )
#             db.session.add(quantified_ingredient)
#             db.session.commit()

    
#     # # Process ingredients and quantified ingredients
#     # existing_ingredients = request.form.getlist('existing_ingredients[]')
#     # new_ingredients = request.form.getlist('new_ingredients[]')
#     # quantities = request.form.getlist('quantities[]')

#     # for existing_ingredient_id, new_ingredient, quantity in zip(existing_ingredients, new_ingredients, quantities):
#     #     if existing_ingredient_id:
#     #         # Use an existing ingredient
#     #         existing_ingredient = Ingredient.query.get(existing_ingredient_id)
#     #         new_recipe.ingredients.append(existing_ingredient)
            
#     #         # Create QuantifiedIngredient
#     #         quantified_ingredient = QuantifiedIngredient(quantity=quantity, ingredient=existing_ingredient)
#     #         db.session.add(quantified_ingredient)
#     #     elif new_ingredient:
#     #         # Create a new ingredient and use it
#     #         new_ingredient_obj = Ingredient(name=new_ingredient, recipe=new_recipe)
#     #         db.session.add(new_ingredient_obj)
#     #         new_recipe.ingredients.append(new_ingredient_obj)

#     #         # Create QuantifiedIngredient for the new ingredient
#     #         quantified_ingredient = QuantifiedIngredient(quantity=quantity, ingredient=new_ingredient_obj)
#     #         db.session.add(quantified_ingredient)

#     # # Save cooking steps
#     # # new_recipe.steps = cooking_steps
    
#     # db.session.commit()

#         return redirect(url_for("main.recipe", recipe_id=new_recipe.id))

#     # For GET requests, render the recipe creation form
#     ingredients = model.Ingredient.query.all()
#     return render_template("create_recipe.html", ingredients=ingredients)



# @bp.route("/recipe/<int:recipe_id>")
# @flask_login.login_required
# def recipe(recipe_id):
#     # goes to table w/ recipes and looks for recipe id 
#     recipe = db.session.get(model.Recipe, recipe_id)
#     if not recipe:
#         abort(404, "Recipe id {} doesn't exist.".format(recipe_id))
    
#     query =  db.select(model.Recipe).where(model.Recipe.id == recipe_id)
#     recipe = db.get_or_404(model.Recipe, recipe_id)


#     return render_template("main/recipe.html", recipe=recipe)






 