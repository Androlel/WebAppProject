from . import db
import flask_login

# HAVE NOT UPDATED FOR PROJECT YET
# since following people is a many to many relationship we have a relationship from the table to itself
class FollowingAssociation(db.Model):
    follower_id = db.Column(
        db.Integer, db.ForeignKey("user.id"), primary_key=True, nullable=False
    )
    followed_id = db.Column(
        db.Integer, db.ForeignKey("user.id"), primary_key=True, nullable=False
    )


class User(flask_login.UserMixin, db.Model):
   # checked: 
    id = db.Column(db.Integer, primary_key=True)

    email = db.Column(db.String(128), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    name = db.Column(db.String(64), nullable=False)

    recipes = db.relationship('Recipe', back_populates='user')
    ratings = db.relationship('Rating', back_populates='user')
    bookmarks = db.relationship('Bookmark', back_populates='user')
    photos = db.relationship('Photo', back_populates='user')
   
   
   # haven't implemented yet:
    messages = db.relationship('Message', back_populates='user')
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


class Recipe(db.Model):
   # checked
    id = db.Column(db.Integer, primary_key=True)
   
    title = db.Column(db.String(512), nullable=False)
    description = db.Column(db.String(512), nullable=False)

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user = db.relationship('User', back_populates='recipes')

    servings = db.Column(db.Integer, nullable=False)
    time = db.Column(db.Integer, nullable=False) # in minutes 

    quantified_ingredients = db.relationship('QuantifiedIngredient', back_populates='recipe')
    steps = db.relationship('Step', back_populates='recipe')
    ratings = db.relationship('Rating', back_populates='recipe')
    bookmarks = db.relationship('Bookmark', back_populates='recipe')
    photos = db.relationship('Photo', back_populates='recipe')
   
class Ingredient(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    # name of ingredient 
    name = db.Column(db.String(256), nullable=False)

    quantified_ingredients = db.relationship('QuantifiedIngredient', back_populates='ingredient')

class QuantifiedIngredient(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    quantity = db.Column(db.Integer, nullable=False)
    unit = db.Column(db.String(64), nullable=False)

    recipe_id = db.Column(db.Integer, db.ForeignKey('recipe.id'), nullable=False)
    recipe = db.relationship('Recipe', back_populates='quantified_ingredients')

    ingredient_id = db.Column(db.Integer, db.ForeignKey('ingredient.id'), nullable=False)
    ingredient = db.relationship('Ingredient', back_populates='quantified_ingredients')
    
class Step(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    number = db.Column(db.Integer, nullable=False)
    description = db.Column(db.String(512), nullable=False)

    recipe_id = db.Column(db.Integer, db.ForeignKey('recipe.id'), nullable=False)
    recipe = db.relationship('Recipe', back_populates='steps')

class Rating(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    # for now we'll just do up/down vote
   # do i need () for Boolean?? 
    value = db.Column(db.Boolean(), nullable=False)

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user = db.relationship('User', back_populates='ratings')

    recipe_id = db.Column(db.Integer, db.ForeignKey('recipe.id'), nullable=False)
    recipe = db.relationship('Recipe', back_populates='ratings')


class Bookmark(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user = db.relationship('User', back_populates='bookmarks')

    recipe_id = db.Column(db.Integer, db.ForeignKey('recipe.id'), nullable=False)
    recipe = db.relationship('Recipe', back_populates='bookmarks')


class Photo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
   # any user can upload photos even if they didn't create recipe 
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user = db.relationship('User', back_populates='photos')

    recipe_id = db.Column(db.Integer, db.ForeignKey('recipe.id'), nullable=False)
    recipe = db.relationship('Recipe', back_populates='photos') 
   # NEED TO INLCUDE PHOTO TOO LOOK AT EXAMPLE CODE 
   


# NOT ALTERED FOR PROJECT YET
class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user = db.relationship('User', back_populates='messages')
    text = db.Column(db.String(512), nullable=False)
    timestamp = db.Column(db.DateTime(), nullable=False)
    response_to_id = db.Column(db.Integer, db.ForeignKey('message.id'))
    response_to = db.relationship('Message', back_populates='responses', remote_side=[id])
    responses = db.relationship('Message', back_populates='response_to', remote_side=[response_to_id])

