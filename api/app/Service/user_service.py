from app.Repository.user_repository import UserRepository
class UserService:
    @staticmethod
    def create_user(user_data,db):
        return UserRepository.create_user(user_data,db)
