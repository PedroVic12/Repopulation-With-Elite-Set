import 'package:postgres/postgres.dart';
import 'package:vaden/vaden.dart';

@Configuration()
class PostgresConfiguration {
  @Bean()
  Future<Connection> connection(ApplicationSettings settings) {
    SslMode sslAdapter(String? ssl) {
      return switch (ssl) {
        'disable' => SslMode.disable,
        'require' => SslMode.require,
        'verifyFull' => SslMode.verifyFull,
        _ => SslMode.disable,
      };
    }

    return Connection.open(
      Endpoint(
        host: settings['postgres']['host'],
        database: settings['postgres']['database'],
        port: settings['postgres']['port'],
        username: settings['postgres']['username'],
        password: settings['postgres']['password'],
      ),
      settings:
          ConnectionSettings(sslMode: sslAdapter(settings['postgres']['ssl'])),
    );
  }
}
