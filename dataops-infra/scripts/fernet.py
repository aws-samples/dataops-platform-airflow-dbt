from cryptography.fernet import Fernet

if __name__ == "__main__":
    print("This is your Fernet key: ", Fernet.generate_key().decode())
