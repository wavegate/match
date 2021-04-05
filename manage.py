from flask_script import Manager
from flask_script import Command

app = Flask(__name__)
# configure your app

manager = Manager(app)

if __name__ == "__main__":
	manager.add_command('hello', Hello())
    manager.run()

   class Hello(Command):
    "prints hello world"

    def run(self):
        print "hello world"

@manager.command
def seed():
	