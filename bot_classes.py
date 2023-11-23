class User():
    def __init__(self):
        self.flag = 0

    # def update_name(self, name, id):
    #     self.name = name
    #     self.id = id

    # def update_surname(self, surname):
    #     self.surname = surname

    # def update_token(self, token):
    #     self.token = token

    # def update_email(self, email):
    #     self.email = email

    def update_all(self, name, surname, token, email, id):
        self.name = name
        self.id = id
        self.surname = surname
        self.token = token
        self.email = email


    def change_for_owner(self):
        self.flag = 1
        owner = Owner()
        owner.load_info(self.name, self.surname, self.token, self.email, self.id)
        return owner

    def update_flag_access(self, flag):
        self.flag_access = flag

class Owner():
    def __init__(self):
        self.flag = 0

    def load_info(self, name, surname, token, email, id):
        self.name = name
        self.surname = surname
        self.token = token
        self.id = id
        self.email = email