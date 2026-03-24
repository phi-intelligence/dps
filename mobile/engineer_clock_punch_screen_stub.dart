// Flutter stub (non-runnable in this repo unless you add a Flutter project).
// Purpose: document the intended engineer clock-in/out UI and payload mapping.

import 'package:flutter/material.dart';

class EngineerClockPunchScreenStub extends StatefulWidget {
  const EngineerClockPunchScreenStub({super.key});

  @override
  State<EngineerClockPunchScreenStub> createState() => _EngineerClockPunchScreenStubState();
}

class _EngineerClockPunchScreenStubState extends State<EngineerClockPunchScreenStub> {
  final jobIdController = TextEditingController();
  final latitudeController = TextEditingController(text: "51.5074");
  final longitudeController = TextEditingController(text: "-0.1278");

  bool busy = false;
  String? lastResponse;

  @override
  void dispose() {
    jobIdController.dispose();
    latitudeController.dispose();
    longitudeController.dispose();
    super.dispose();
  }

  Map<String, dynamic> buildPunchPayload() {
    return {
      "job_id": jobIdController.text.trim(),
      "latitude": double.tryParse(latitudeController.text.trim()) ?? 0.0,
      "longitude": double.tryParse(longitudeController.text.trim()) ?? 0.0,
      // Optional:
      // "occurred_at": DateTime.now().toIso8601String(),
      // "offline_device_id": "optional-offline-id",
    };
  }

  Future<void> punchIn() async {
    setState(() {
      busy = true;
      lastResponse = null;
    });

    // TODO:
    // - Read JWT token from secure storage
    // - POST to POST /time/punch/in
    // - Authorization: Bearer <token>
    // - Show response and validation errors
    //
    // Endpoint expects:
    // { job_id, latitude, longitude, occurred_at?, offline_device_id? }
    await Future.delayed(const Duration(milliseconds: 300));

    setState(() {
      busy = false;
      lastResponse = "Stub punch-in. Implement API call to /time/punch/in.";
    });
  }

  Future<void> punchOut() async {
    setState(() {
      busy = true;
      lastResponse = null;
    });

    // TODO:
    // - POST to POST /time/punch/out
    // - Same payload shape as punch-in
    await Future.delayed(const Duration(milliseconds: 300));

    setState(() {
      busy = false;
      lastResponse = "Stub punch-out. Implement API call to /time/punch/out.";
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text("Clock In / Out (Engineer - Stub)")),
      body: Padding(
        padding: const EdgeInsets.all(16),
        child: ListView(
          children: [
            TextField(
              controller: jobIdController,
              decoration: const InputDecoration(labelText: "job_id"),
            ),
            TextField(
              controller: latitudeController,
              decoration: const InputDecoration(labelText: "Latitude"),
              keyboardType: TextInputType.number,
            ),
            TextField(
              controller: longitudeController,
              decoration: const InputDecoration(labelText: "Longitude"),
              keyboardType: TextInputType.number,
            ),
            const SizedBox(height: 12),
            Row(
              children: [
                Expanded(
                  child: ElevatedButton(
                    onPressed: busy ? null : punchIn,
                    child: busy ? const Text("Working...") : const Text("Punch In"),
                  ),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: ElevatedButton(
                    onPressed: busy ? null : punchOut,
                    child: busy ? const Text("Working...") : const Text("Punch Out"),
                  ),
                ),
              ],
            ),
            if (lastResponse != null) ...[
              const SizedBox(height: 12),
              Text(lastResponse!, style: const TextStyle(fontSize: 14)),
            ],
            const SizedBox(height: 16),
            const Text(
              "Geofence validation happens server-side.\n"
              "Engineer tokens can call /time/punch/in and /time/punch/out.",
              style: TextStyle(color: Colors.grey),
            ),
          ],
        ),
      ),
    );
  }
}

