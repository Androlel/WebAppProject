from . import db
import flask_login

# since following people is a many to many relationship we have a relationship from the table to itself
class FollowingAssociation(db.Model):
    follower_id = db.Column(
        db.Integer, db.ForeignKey("user.id"), primary_key=True, nullable=False
    )
    followed_id = db.Column(
        db.Integer, db.ForeignKey("user.id"), primary_key=True, nullable=False
    )


# both extend SQLAlchemy model class
# userMixIn users of app are represented by this class, for flask login
class User(flask_login.UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(128), unique=True, nullable=False)
    name = db.Column(db.String(64), nullable=False)
    password = db.Column(db.String(100), nullable=False)
    messages = db.relationship('Message', back_populates='user')

   # not sure if user supposed to have rating
    rating = db.relationship('Rating', back_populates='user')

    recipe = db.relationship('Recipe', back_populates='user')
   
   
    following = db.relationship(
        "User",
        secondary=FollowingAssociation.__table__,
        primaryjoin=FollowingAssociation.follower_id == id,# left side of the user, who the user is follower of 
        secondaryjoin=FollowingAssociation.followed_id == id,# who the user is followed by
        back_populates="followers",
    )
    followers = db.relationship(
        "User",
        secondary=FollowingAssociation.__table__,
        primaryjoin=FollowingAssociation.followed_id == id,
        secondaryjoin=FollowingAssociation.follower_id == id,
        back_populates="following",
    )

class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user = db.relationship('User', back_populates='messages')
    text = db.Column(db.String(512), nullable=False)
    timestamp = db.Column(db.DateTime(), nullable=False)
    response_to_id = db.Column(db.Integer, db.ForeignKey('message.id'))
    response_to = db.relationship('Message', back_populates='responses', remote_side=[id])
    responses = db.relationship('Message', back_populates='response_to', remote_side=[response_to_id])

# not sure what to put in parameter 
class Recipe(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(512), nullable=False)
    description = db.Column(db.String(512), nullable=False)
    user = db.relationship('User', db.ForeignKey('user'), back_populates='recipe')
    servings = db.Column(db.Integer, nullable=False)
    time = db.Column(db.Integer, nullable=False) # in minutes 
   # need secondary? have multple ingredients in each recipe
    ingredients = db.relationship('Ingredient', back_populates='recipes')
    quantified_ingredients = db.relationship('QuantifiedIngredient', back_populates='recipe')
    steps = db.relationship('Step', back_populates='recipe')
   # many to one relationship with rating and recipe
    rating = db.relationship('Rating', back_populates='recipe')

class Ingredient(db.Model):
   id = db.Column(db.Integer, primary_key=True)
   recipe = db.relationship('Recipe', back_populates='ingredients')
  # name of ingredient 
   name = db.Column(db.String(128), nullable=False)
  # how much, number + unit (ex: 1 cup) 
   quantified_ingredients = db.relationship('QuantifiedIngredients', back_populates='ingredient')

class QuantifiedIngredient(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    quantity = db.Column(db.Integer, nullable=False)
    unit = db.Column(db.String(64), nullable=False)

   # not sure if need to add relationship to receipes since ingredient already does 
 # changed from Recipes to Recipe  
    recipes = db.relationship('Recipes', back_populates='quantified_ingredients')
    recipes_id = db.Column(db.Integer, db.ForeignKey('recipes.id'), nullable=False)
    
    ingredient = db.relationship('Ingredient', back_populates='quantified_ingredients')
    ingredient_id = db.Column(db.Integer, db.ForeignKey('ingredients.id'), nullable=False)
    

class Step(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    number = db.Column(db.Integer, nullable=False)
    description = db.Column(db.String(512), nullable=False)

    recipe_id = db.Column(db.Integer, db.ForeignKey('recipe.id'), nullable=False)
    recipe = db.relationship('Recipe', back_populates='step')

class Rating(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    # for now we'll just do up/down vote
    value = db.Column(db.Boolean(), nullable=False)

   # not sure if supposed to rate user 
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user = db.relationship('User', db.ForeignKey('user.id'), back_populates='rating')

    recipe_id = db.Column(db.Integer, db.ForeignKey('recipe.id'), nullable=False)
    recipe = db.relationship('Recipe', db.ForeignKey('recipe.id'), back_populates='rating')

# class Bookmark(db.Model):

# finish checking each relationship has a column with the id and foreign key 


