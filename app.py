import subprocess

def run_command(user_input):
    subprocess.run(user_input, shell=True)

user_input = input("Enter command: ")
run_command(user_input)