import datetime
import dateutil.tz
from . import db
from flask import Blueprint, render_template, redirect, request, url_for, abort
from . import model
import flask_login
from flask_login import current_user
import pathlib
from flask import current_app

bp = Blueprint("main", __name__)

   # currently only showing 1 recipe, should be 10  
# @flask_login.login_required
@bp.route("/")
def index():
    query = db.select(model.Recipe).where(model.Recipe.id == '1')
    test_recipe = db.session.execute(query).scalar()


    recipes =[
        test_recipe
    ]
   #Our mehtods of finding a recipe are slightly diffrent
   #   
    #     followers = db.aliased(model.User)
    # # query = (
    # #     db.select(model.Recipe)
    # #     .join(model.User)
    # #     .join(followers, model.User.followers)
    # #     .where(followers.id == flask_login.current_user.id)
    # #     .where(model.Message.response_to == None)
    # #     .order_by(model.Message.timestamp.desc())
    # #     .limit(1)
    # # )
    # query = (
    #     db.select(model.Recipe).limit(10)
    # ) 
    # recipes = db.session.query(model.Recipe).limit(10).all()

    return render_template("main/index.html", recipes=recipes)

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
            ingredients=new_ingredients,
            steps=cooking_steps,
        )
        db.session.add(new_recipe)
        db.session.commit()

    return render_template("recipes/edit_recipe.html", recipe=recipe)


# controller function for displaying the current state of the recipe and asking for the next ingredient or step
# represents controller receiving the data about an ingredient and quantity, and storing them as well
# coult be a source of problems^^ 
@bp.route("/edit_recipe/add_ingredients/<int:recipe_id>", methods=["GET", "POST"])
@flask_login.login_required
def edit_recipe_add_ingredients(recipe_id):
    recipe = model.Recipe.query.get_or_404(recipe_id)

    if request.method == "POST":
        ingredient_name = request.form.get("ingredient_name")
        print("Here is the ingredient_name: ", ingredient_name)
        quantity = request.form.get("quantity")
        unit = request.form.get("unit")
        
        existing_ingredient = db.session.execute(
            db.select(model.Ingredient).where(model.Ingredient.name==ingredient_name)
        ).scalars().one_or_none()
        print("HERE IS THE Existing ingredient: ", existing_ingredient)
        if existing_ingredient:
            print("reusing ingredient")
           # ingredient already exists in database so use that
            # Create a new quantified ingredient and associate it with the ingredient 
            new_quantified_ingredient = model.QuantifiedIngredient(
                recipe=recipe,
                quantity=quantity,
                unit=unit,
                ingredient=existing_ingredient,
            )
            
           
        else:
            print("DOESN'T EXIST SO creating new ingredient!")
            print("")
            
           # ingredient doesnt exist so make new one 
            # Create a new ingredient and associate it with the recipe

           # having issues with creating new ingredient 
            
#ISSUE HERE
            new_ingredient = model.Ingredient(name=ingredient_name, id=100)
            print(new_ingredient)
            db.session.add(new_ingredient)
            db.session.commit()

            new_quantified_ingredient = model.QuantifiedIngredient(
                recipe=recipe,
                quantity=quantity,
                unit=unit,
                ingredient=new_ingredient,
            )
            db.session.add(new_quantified_ingredient)
                
        # db.session.add(new_quantified_ingredient)

        import pdb; pdb.set_trace()
        recipe.quantified_ingredients.append(new_quantified_ingredient)
        
        db.session.commit()

        return redirect(url_for('main.edit_recipe_add_ingredients', recipe_id=recipe_id))

    return render_template("recipes/edit_recipe.html", recipe=recipe)

@bp.route("/edit_recipe/delete_ingredients/<int:recipe_id>", methods=["GET", "POST"])
@flask_login.login_required
def edit_recipe_delete_ingredients(recipe_id):
    recipe = model.Recipe.query.get_or_404(recipe_id)

    if request.method == "POST":
        quantifiend_ingredient_id_to_delete = request.form.get("quantifiend_ingredient_id_to_delete")
        
        # Find the step with the given step number
        quantified_ingredient_to_delete = db.session.execute(
            db.select(model.QuantifiedIngredient).where(model.QuantifiedIngredient.id==quantifiend_ingredient_id_to_delete).where
            (model.QuantifiedIngredient.recipe==recipe)
        ).scalars().one_or_none()

       
        if quantified_ingredient_to_delete:
            db.session.delete(quantified_ingredient_to_delete)
            db.session.commit()

        return redirect(url_for('main.edit_recipe_delete_ingredients', recipe_id=recipe_id))

    return render_template("recipes/edit_recipe.html", recipe=recipe)


# controller function for receiving the data about a step, and storing it
@bp.route("/edit_recipe/add_steps/<int:recipe_id>", methods=["GET", "POST"])
@flask_login.login_required
def edit_recipe_add_steps(recipe_id):
    recipe = model.Recipe.query.get_or_404(recipe_id)

    if request.method == "POST":
        print("its a post!")
        print("adding step")
        step_description = request.form.get("step_description")
        step_number = request.form.get("number")

        # Create a new step and associate it with the recipe
        new_step = model.Step(
            number=step_number, 
            description=step_description, 
            recipe=recipe
            )
        db.session.add(new_step)
        recipe.steps.append(new_step)
        db.session.commit()

        return redirect(url_for('main.edit_recipe_add_steps', recipe_id=recipe_id))

    return render_template("recipes/edit_recipe.html", recipe=recipe)

    # controller function for receiving the data about a step, and storing it
@bp.route("/edit_recipe/delete_steps/<int:recipe_id>", methods=["GET", "POST"])
@flask_login.login_required
def edit_recipe_delete_steps(recipe_id):
    recipe = model.Recipe.query.get_or_404(recipe_id)

    if request.method == "POST":
        print("its a post!")

        print("inside delete_step")
        # Handle deleting a step by its step number
        step_number_to_delete = request.form.get("step_number_to_delete")
        print(step_number_to_delete)
        # Find the step with the given step number
        step_to_delete = db.session.execute(
            db.select(model.Step).where(model.Step.number==step_number_to_delete).where(model.Step.recipe==recipe)
        ).scalars().one_or_none()
       # next((step for step in recipe.steps if step.number == step_number_to_delete), None)
       # import pdb; pdb.set_trace()
        if step_to_delete:
            # Remove the step from the recipe and delete it from the database
           # recipe.steps.remove(step_to_delete)
            db.session.delete(step_to_delete)
            db.session.commit()

        return redirect(url_for('main.edit_recipe_delete_steps', recipe_id=recipe_id))

    return render_template("recipes/edit_recipe.html", recipe=recipe)

# controller function for marking the recipe as complete
# routes.py
@bp.route("/complete_recipe/<int:recipe_id>", methods=["POST"])
@flask_login.login_required
def complete_recipe(recipe_id):
    recipe = model.Recipe.query.get_or_404(recipe_id)

    recipe.complete = True
    db.session.commit()
    return render_template("recipes/recipe_template.html", recipe=recipe)

def get_quanitiy(ingredient_id):
    query = db.select(model.QuantifiedIngredient).where(model.QuantifiedIngredient.ingredient_id == ingredient_id)
    quantity = db.session.execute(query).scalar()

    return quantity

@bp.route('/bookmark/<int:recipe_id>', methods=['POST'])
@flask_login.login_required
def bookmark(recipe_id):
    print("button pressed")
    query = db.select(model.Recipe).where(model.Recipe.id == recipe_id)
    recipe = db.session.execute(query).scalar()

    print(recipe.id, recipe_id)

    # query = db.select(model.User).where(model.User.id == user_id)
    # user = db.session.execute(query).scalar()
    user = flask_login.current_user
    # query = db.select(model.Recipe).where(model.Recipe.id == '124')
    # test_recipe = db.session.execute(query).scalar()
    # obj = session.query(ObjectRes).order_by(ObjectRes.id.desc()).first()
    query = db.select(model.Bookmark).where(model.Bookmark.user_id==user.id).where(model.Bookmark.recipe_id==recipe_id)
    bookmark_exists = db.session.execute(query).scalar()
    print(bookmark_exists)
    if bookmark_exists != None:
        print('duplicate')
        return redirect(url_for('main.display_recipe', recipe_id=recipe_id))


    query = db.session.query(model.Bookmark).order_by(model.Bookmark.id.desc()).first()
    if query != None:
        id = query.id + 1 
    else:
        id = 1  
    
    bookmark = model.Bookmark(
        id = id,
        recipe=recipe,
        recipe_id=recipe_id,
        user=user,
        user_id = user.id
    )

    db.session.add(bookmark)
    db.session.commit()


    print(bookmark.id)
    print(bookmark.recipe_id)
    
    return redirect(url_for('main.display_recipe', recipe_id=recipe_id))

@bp.route('/recipe/<int:recipe_id>')
def display_recipe(recipe_id):
    query = db.select(model.Recipe).where(model.Recipe.id == recipe_id)
    recipe = db.session.execute(query).scalar()

    print('get to recipe page')
    return render_template("recipes/recipe_template.html", recipe=recipe)

@bp.route('/rate/<int:rating>/<int:recipe_id>', methods=['POST'])
@flask_login.login_required
def rate(rating,recipe_id):
    print(rating)
    if rating == 1:
        boolRating = True
    else:
        boolRating = False

    query = db.session.query(model.Bookmark).order_by(model.Bookmark.id.desc()).first()
    if query != None:
        id = query.id + 1 
    else:
        id = 1 

    
    user = flask_login.current_user
    query = db.select(model.Recipe).where(model.Recipe.id == recipe_id)
    recipe = db.session.execute(query).scalar()

    #Checking for dupe then swapping
    query = db.select(model.Rating).where(model.Rating.user_id == user.id).where(model.Rating.recipe_id == recipe_id)
    duplicate = db.session.execute(query).scalar()

    if duplicate !=  None:
       #If the rating switched 
        if duplicate.value != rating:
            duplicate.value = rating
            db.session.commit()
            print('swap')
        return redirect(url_for('main.display_recipe', recipe_id=recipe_id))


    new_rating = model.Rating(
        id = id,
        value = boolRating,
        user_id = user.id,
        # user=user,
        recipe_id=recipe_id,
        # recipe=recipe
    )

    db.session.add(new_rating)
    db.session.commit()
    return 'Rated'

def getLikes(recipe_id):
    query = db.select(model.Rating).where(model.Rating.recipe_id == recipe_id).where(model.Rating.value == 1)
    listOfLikes = db.session.execute(query).scalars().all()

    if listOfLikes != None:
        likes = len(listOfLikes)
        print(likes)
        print(listOfLikes)
        return likes
    else:
        return 0
    
def getDislikes(recipe_id):
    query = db.select(model.Rating).where(model.Rating.recipe_id == recipe_id).where(model.Rating.value == 0)
    listOfDislikes = db.session.execute(query).scalars().all()

    if listOfDislikes != None:
        dislikes = len(listOfDislikes)
        print(dislikes)
        print(listOfDislikes)
        return dislikes
    else:
        return 0

@bp.route('/upload/<int:recipe_id>', methods=['POST'])
@flask_login.login_required   
def upload_photo(recipe_id):
    uploaded_file = request.files["photo"]
    if uploaded_file.filename != "":
        content_type = uploaded_file.content_type
        if content_type == "image/png":
            file_extension = "png"
        elif content_type == "image/jpeg":
            file_extension = "jpg"
        else:
            abort(400, f"Unsupported file type {content_type}")

        query = db.select(model.Recipe).where(model.Recipe.id == recipe_id)
        recipe = db.session.execute(query).scalar()

        photo = model.Photo(
            user=flask_login.current_user,
            recipe=recipe,
            file_extension=file_extension
        )
        db.session.add(photo)
        db.session.commit()

        path = (
            pathlib.Path(current_app.root_path)
            / "static"
            / "photos"
            / f"photo-{photo.id}.{file_extension}"
        )
        uploaded_file.save(path)
        return redirect(url_for('main.display_recipe', recipe_id=recipe_id))
    
    return redirect(url_for('main.display_recipe', recipe_id=recipe_id))
    
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






 