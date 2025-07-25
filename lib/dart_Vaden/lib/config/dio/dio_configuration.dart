import 'package:dio/dio.dart';
import 'package:vaden/vaden.dart';

@Configuration()
class DioConfiguration {
  @Bean()
  Dio dioApoiaseConfig(ApplicationSettings settings) {
    return Dio(
      BaseOptions(
        baseUrl: settings['env']['base_url'],
        headers: {},
      ),
    );
  }
}
