import 'package:dart_vaden_app/pages/my_home_page.dart';
import 'package:flutter/material.dart';
import 'package:dart_vaden_app/vaden_application.dart';

// flutter pub add flutter_vaden dio vaden

void main() {
  runApp(VadenApp(child: const MyApp()));
}

class MyApp extends StatelessWidget {
  const MyApp({super.key});

  // This widget is the root of your application.
  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'My App',
      debugShowCheckedModeBanner: false,
      darkTheme: ThemeData(
        colorScheme: ColorScheme.fromSeed(
          seedColor: const Color.fromARGB(255, 0, 31, 208),
        ),
      ),
      themeMode: ThemeMode.system,
      // lightTheme: ThemeData.light(),
      theme: ThemeData(
        colorScheme: ColorScheme.fromSeed(seedColor: Colors.lime),
      ),
      home: const MyHomePage(title: 'Flutter Dart Vaden Getx Home Page'),
    );
  }
}
