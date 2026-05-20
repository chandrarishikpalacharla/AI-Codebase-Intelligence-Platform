from app.Model.user_model import User

class UserRepository:

    @staticmethod
    def create_user(user_data, db):

        user = User(
            username=user_data.username,
            email=user_data.email
        )

        db.add(user)

        db.commit()

        db.refresh(user)

        return user