import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:flutter_vaden/flutter_vaden.dart';

// Modelo para Pokémon (simples)
class PokemonModel {
  final String name;
  final int baseHp;

  PokemonModel({required this.name, required this.baseHp});

  factory PokemonModel.fromJson(Map<String, dynamic> json) {
    return PokemonModel(
      name: json['name'],
      baseHp: json['stats'][0]['base_stat'],
    );
  }
}

@Configuration()
class DioConfiguration {
  @Bean()
  Dio dioFactory() {
    final dio = Dio(BaseOptions(baseUrl: 'https://pokeapi.co/api/v2/'));
    dio.interceptors.add(LogInterceptor(responseBody: true));
    return dio;
  }
}

// API Client Vaden para PokeAPI
@ApiClient()
abstract class PokemonApi {
  @Get('/pokemon/<name>')
  Future<Map<String, dynamic>> getPokemon(@Param() String name);
}

class PokeHomePage extends StatefulWidget {
  const PokeHomePage({super.key});

  @override
  State<PokeHomePage> createState() => _PokeHomePageState();
}

// ...existing code...
class _PokeHomePageState extends State<PokeHomePage> {
  final TextEditingController poke1Ctrl = TextEditingController(
    text: 'pikachu',
  );
  final TextEditingController poke2Ctrl = TextEditingController(
    text: 'bulbasaur',
  );
  String resultText = 'Pronto para batalhar!';
  bool loading = false;

  String? poke1Image;
  String? poke2Image;

  Future<void> battlePokemons() async {
    setState(() {
      loading = true;
      resultText = 'Carregando...';
      poke1Image = null;
      poke2Image = null;
    });
    try {
      final pokeApi = context.read<PokemonApi>();
      print('PokeAPI: $pokeApi');
      final data1 = await pokeApi.getPokemon(
        poke1Ctrl.text.trim().toLowerCase(),
      );
      final data2 = await pokeApi.getPokemon(
        poke2Ctrl.text.trim().toLowerCase(),
      );

      print('Poke1: $data1');
      print('Poke2: $data2');
      final poke1 = PokemonModel.fromJson(data1);
      final poke2 = PokemonModel.fromJson(data2);

      poke1Image = data1['sprites']?['front_default'];
      poke2Image = data2['sprites']?['front_default'];

      String winner;
      if (poke1.baseHp > poke2.baseHp) {
        winner = poke1.name;
      } else if (poke2.baseHp > poke1.baseHp) {
        winner = poke2.name;
      } else {
        winner = 'Empate!';
      }

      setState(() {
        resultText =
            'Batalha: ${poke1.name} vs ${poke2.name}\nHP: ${poke1.baseHp} vs ${poke2.baseHp}\nVencedor: $winner';
        loading = false;
      });
    } catch (e) {
      setState(() {
        resultText = 'Erro na batalha: $e';
        loading = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Pokémon Battle')),
      body: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            TextField(
              controller: poke1Ctrl,
              decoration: const InputDecoration(labelText: 'Pokémon 1'),
            ),
            TextField(
              controller: poke2Ctrl,
              decoration: const InputDecoration(labelText: 'Pokémon 2'),
            ),
            const SizedBox(height: 20),
            Row(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                if (poke1Image != null) Image.network(poke1Image!, height: 80),
                const SizedBox(width: 24),
                if (poke2Image != null) Image.network(poke2Image!, height: 80),
              ],
            ),
            const SizedBox(height: 20),
            ElevatedButton(
              onPressed: loading ? null : battlePokemons,
              child: loading
                  ? const CircularProgressIndicator()
                  : const Text('Batalhar'),
            ),
            const SizedBox(height: 20),
            Text(
              resultText,
              style: Theme.of(context).textTheme.bodyLarge,
              textAlign: TextAlign.center,
            ),
          ],
        ),
      ),
    );
  }
}
// ...existing code...