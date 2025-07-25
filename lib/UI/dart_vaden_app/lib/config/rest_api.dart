import 'package:dio/dio.dart';
import 'package:flutter_vaden/flutter_vaden.dart';

class ProductDTO {}

@Configuration()
class ApiServiceConfiguration {
  @Bean()
  Dio dio() {
    final dio = Dio(BaseOptions(baseUrl: 'https://pokeapi.co/api/v2/type/3'));
    dio.interceptors.add(LogInterceptor(responseBody: true));
    return dio;
  }
}

@ApiClient()
abstract class ProductApi {
  @Get('/product/<id>')
  Future<ProductDTO> getProduct(@Param() int id);

  @Post('/product')
  Future<ProductDTO> createProduct(@Body() ProductDTO product);

  @Put('/product/<id>')
  Future<ProductDTO> updateProduct(@Param() int id, @Body() ProductDTO product);

  @Delete('/product/<id>')
  Future<void> deleteProduct(@Param() int id);

  @Get('/products')
  Future<List<ProductDTO>> getAllProducts();
}
