# template 1

from flask import Flask
from config import Config
from flask import render_template

appname = "IOT - sample1"
app = Flask(appname)
myconfig = Config
app.config.from_object(myconfig)

elenco=[]

@app.route('/')
def testoHTML():
    return '<h1>I love IoT</h1>'


@app.route('/lista', methods=['GET'])
def stampalista():
    return render_template('lista.html', lista=elenco)

@app.route('/addinlista/<name>', methods=['POST'])
def addinlista(name):
    elenco.append(name)
    return str(len(elenco))



if __name__ == '__main__':
    port = 80
    interface = '0.0.0.0'
    app.run(host=interface,port=port)