from twisted.internet import reactor
from twisted.internet.protocol import ServerFactory, connectionDone
from twisted.protocols.basic import LineOnlyReceiver
import time


class ServerProtocol(LineOnlyReceiver):
    factory: 'Server'
    login: str = None
    messages: list = []

    def connectionMade(self):
        # Потенциальный баг для внимательных =)
        self.messages = []
        self.factory.clients.append(self)

    def connectionLost(self, reason=connectionDone):
        self.factory.clients.remove(self)

    def lineReceived(self, line: bytes):
        content = line.decode()

        if self.login is not None:
            content = f"Message from {self.login}: {content}"

            for user in self.factory.clients:
                if user is not self:
                    user.sendLine(content.encode())
                else:
                    message = {'content': content, 'time': time.time()}
                    user.messages.append(message)
        else:
            # login:admin -> admin
            if content.startswith("login:"):
                self.login = content.replace("login:", "")
                if self.login in [user.login for user in self.factory.clients if user is not self]:
                    self.sendLine("Login is Unused".encode())
                    self.transport.loseConnection()
                else:
                    self.sendLine(f"Welcome {self.login}!".encode())
                    self.send_history()
            else:
                self.sendLine("Invalid login".encode())

    def send_history(self):
        messages = []
        for user in self.factory.clients:
            messages.extend(user.messages)

        messages = sorted(messages, key=lambda k: k['time'], reverse=False)
        for message in messages[-10:]:
            self.sendLine(message['content'].encode())


class Server(ServerFactory):
    protocol = ServerProtocol
    clients: list

    def startFactory(self):
        self.clients = []
        print("Server started")

    def stopFactory(self):
        print("Server closed")


reactor.listenTCP(1234, Server())
reactor.run()
