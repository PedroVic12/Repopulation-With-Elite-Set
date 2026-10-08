#include <QGuiApplication>
#include <QQmlApplicationEngine>
#include <QQmlContext>
#include <QObject>
#include <QDebug>

class SystemBridge : public QObject {
    Q_OBJECT
    Q_PROPERTY(QString currentUser READ currentUser CONSTANT)

public:
    explicit SystemBridge(QObject *parent = nullptr) : QObject(parent) {}
    QString currentUser() const { return "Pedro"; }

    Q_INVOKABLE void logAction(const QString &actionName) {
        qDebug() << "[C++ Native Core] Ação registrada na tela:" << actionName;
    }
};

int main(int argc, char *argv[]) {
    QGuiApplication app(argc, argv);
    QQmlApplicationEngine engine;

    SystemBridge bridge;
    engine.rootContext()->setContextProperty("Bridge", &bridge);

    engine.load(QUrl::fromLocalFile("src/views/MainApp.qml"));
    if (engine.rootObjects().isEmpty())
        return -1;

    return app.exec();
}
#include "app.moc"
