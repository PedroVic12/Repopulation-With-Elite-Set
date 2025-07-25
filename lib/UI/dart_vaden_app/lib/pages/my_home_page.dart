import 'package:dart_vaden_app/models/product_model.dart';
import 'package:dart_vaden_app/pages/PokeHomePage.dart';
import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:dart_vaden_app/data/api/product_api.dart';
import 'package:flutter_vaden/flutter_vaden.dart';

// Exemplo de outra página recebendo uma função
class OutraPagina extends StatelessWidget {
  final VoidCallback onAcao;
  const OutraPagina({super.key, required this.onAcao});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Outra Página')),
      body: Center(
        child: ElevatedButton(
          onPressed: onAcao,
          child: const Text('Executar função'),
        ),
      ),
    );
  }
}

class MyHomePage extends StatefulWidget {
  const MyHomePage({super.key, required this.title});

  final String title;

  @override
  State<MyHomePage> createState() => _MyHomePageState();
}

class _MyHomePageState extends State<MyHomePage> {
  void _navegarParaOutraPagina() {
    Navigator.of(context).push(
      MaterialPageRoute(
        // builder: (_) => OutraPagina(
        //   onAcao: () {
        //     ScaffoldMessenger.of(context).showSnackBar(
        //       const SnackBar(content: Text('Função passada executada!')),
        //     );
        //   },
        // ),
        builder: (_) => PokeHomePage(),
      ),
    );
  }

  int _counter = 0;

  String text = 'Hello Pedro Victor!';

  // Exemplo de modelagem para consumir uma API de batalha Pokémon
  Future<void> battlePokemons(String pokemon1, String pokemon2) async {
    final dio = context.read<Dio>();
    try {
      // Exemplo de chamada para buscar dados dos dois pokémons
      final response1 = await dio.get(
        'https://pokeapi.co/api/v2/pokemon/$pokemon1',
      );
      final response2 = await dio.get(
        'https://pokeapi.co/api/v2/pokemon/$pokemon2',
      );

      // Aqui você pode criar modelos para os pokémons, mas para simplificar:
      final poke1 = response1.data;
      final poke2 = response2.data;

      // Exemplo simples de "batalha": quem tem mais HP base vence
      final hp1 = poke1['stats'][0]['base_stat'];
      final hp2 = poke2['stats'][0]['base_stat'];
      String winner;
      if (hp1 > hp2) {
        winner = poke1['name'];
      } else if (hp2 > hp1) {
        winner = poke2['name'];
      } else {
        winner = 'Empate!';
      }

      setState(() {
        text =
            'Batalha: ${poke1['name']} vs ${poke2['name']}\n'
            'HP: $hp1 vs $hp2\n'
            'Vencedor: $winner';
      });
    } catch (e) {
      setState(() {
        text = 'Erro na batalha: $e';
      });
    }
  }

  void _incrementCounter() async {
    final p = await context.read<ProductApi>().getTest();
    text =
        '${p.length} products fetched: ${p.map((e) => (e as ProductModel?)?.nome).join(', ')}';

    //print('Fetched products: $text');

    battlePokemons("charmander", "ditto");
    setState(() {
      _counter++;
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        // TRY THIS: Try changing the color here to a specific color (to
        // Colors.amber, perhaps?) and trigger a hot reload to see the AppBar
        // change color while the other colors stay the same.
        backgroundColor: Theme.of(context).colorScheme.inversePrimary,
        // Here we take the value from the MyHomePage object that was created by
        // the App.build method, and use it to set our appbar title.
        title: Text(widget.title),
      ),
      body: Center(
        // Center is a layout widget. It takes a single child and positions it
        // in the middle of the parent.
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: <Widget>[
            Row(
              children: [
                Expanded(
                  child: _pokemonCard(
                    null,
                    'https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/other/official-artwork/4.png',
                    150,
                    true,
                  ),
                ),
                Expanded(
                  child: _pokemonCard(
                    null,
                    'https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/other/official-artwork/132.png',
                    35,
                    false,
                  ),
                ),
              ],
            ),
            const Text('You have pushed the button this many times:'),
            Text(
              '$_counter',
              style: Theme.of(context).textTheme.headlineMedium,
            ),
            Text(
              text,
              style: Theme.of(context).textTheme.headlineMedium,
              strutStyle: StrutStyle(
                fontSize: 20.0,
                height: 1.5,
                leadingDistribution: TextLeadingDistribution.even,
                forceStrutHeight: true,
                fontFamily: 'RobotoMono',
                fontWeight: FontWeight.bold,
              ),
            ),

            ElevatedButton(
              onPressed: _navegarParaOutraPagina,
              child: const Text('Navegar para outra página'),
            ),
          ],
        ),
      ),
      floatingActionButton: FloatingActionButton(
        onPressed: _incrementCounter,
        tooltip: 'Increment',
        child: const Icon(Icons.add),
      ), // This trailing comma makes auto-formatting nicer for build methods.
    );
  }

  Widget _pokemonCard(
    Map<String, dynamic>? poke,
    String? image,
    int hp,
    bool isLeft,
  ) {
    String pokemon1 = 'charmander';
    String pokemon2 = 'ditto';

    return Card(
      elevation: 4,
      child: SizedBox(
        width: 200,
        child: Column(
          children: [
            if (image != null)
              Image.network(image, height: 100, fit: BoxFit.contain),
            Text(
              poke?['name']?.toString().toUpperCase() ??
                  (isLeft ? pokemon1 : pokemon2),
              style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 18),
            ),
            Text("HP: $hp", style: const TextStyle(fontSize: 16)),
          ],
        ),
      ),
    );
  }
}
