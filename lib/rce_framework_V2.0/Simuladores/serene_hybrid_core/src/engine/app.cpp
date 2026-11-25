#include <QGuiApplication>
#include <QQmlApplicationEngine>
#include <QQmlContext>
#include <QObject>
#include <QDebug>
#include <QDir>
#include <QFileInfo>

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

    QString appDir = QCoreApplication::applicationDirPath();
    QString qmlPath = appDir + "/../src/views/MainApp.qml";
    if (!QFileInfo::exists(qmlPath)) {
        qmlPath = appDir + "/src/views/MainApp.qml";
    }
    if (!QFileInfo::exists(qmlPath)) {
        qmlPath = "src/views/MainApp.qml";
    }

    qDebug() << "[C++ Native Core] Carregando QML de:" << qmlPath;
    engine.load(QUrl::fromLocalFile(qmlPath));
    if (engine.rootObjects().isEmpty()) {
        qCritical() << "[Erro C++] Falha ao carregar componente QML!";
        return -1;
    }

    return app.exec();
}
#include "app.moc"
