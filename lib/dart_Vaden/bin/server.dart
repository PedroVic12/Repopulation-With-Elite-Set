import 'package:kyogre_vaden_getx/vaden_application.dart';

Future<void> main(List<String> args) async {
  try {
    print("Starting Vaden application...");
    final vaden = VadenApp();
    await vaden.setup();
    final server = await vaden.run(args);
    print('Server listening on port ${server.port}');
  } on Exception catch (e) {
    print('Error starting Vaden application: $e');
  }
  print("Vaden application started successfully.");
  print("Press Ctrl+C to stop the server.");
}
