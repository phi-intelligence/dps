import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/errors/action_failure_guidance.dart';
import '../../../core/sync/submission_outcome.dart';
import '../../../core/sync/sync_coordinator.dart';
import '../data/inventory_lookup_repository.dart';

/// `POST /jobs/{id}/parts-usage` — items must reference **existing** stock SKUs.
///
/// Backend: `reconcile_parts_usage_submission` raises `ValueError` for unknown SKU.
class JobPartsSubmitScreen extends ConsumerStatefulWidget {
  const JobPartsSubmitScreen({
    super.key,
    required this.jobId,
    required this.minLineItems,
  });

  final String jobId;
  final int minLineItems;

  @override
  ConsumerState<JobPartsSubmitScreen> createState() =>
      _JobPartsSubmitScreenState();
}

class _JobPartsSubmitScreenState extends ConsumerState<JobPartsSubmitScreen> {
  final _rows = <_PartRow>[];
  bool _busy = false;
  String? _error;

  @override
  void initState() {
    super.initState();
    _rows.add(_PartRow());
  }

  Future<void> _submit() async {
    final items = <Map<String, Object>>[];
    for (final r in _rows) {
      final sku = r.skuController.text.trim();
      final q = double.tryParse(r.qtyController.text.trim());
      if (sku.isEmpty) continue;
      if (q == null || q <= 0) {
        setState(() => _error = 'Invalid quantity for SKU $sku');
        return;
      }
      items.add(<String, Object>{
        'sku': sku,
        'quantity': q,
      });
    }
    if (items.length < widget.minLineItems) {
      setState(() => _error =
          'Enter at least ${widget.minLineItems} line item(s) with quantity > 0');
      return;
    }
    setState(() {
      _busy = true;
      _error = null;
    });
    final outcome = await ref.read(syncCoordinatorProvider).submitPartsUsage(
          jobId: widget.jobId,
          items: items,
        );
    if (!mounted) return;
    setState(() => _busy = false);
    if (outcome.isFailed || outcome.isBlocked) {
      final msg = outcome.detailMessage ?? 'Failed';
      final hint = actionFailureGuidance(msg);
      setState(() => _error = hint.isEmpty ? msg : '$msg\n$hint');
      return;
    }
    Navigator.of(context).pop(outcome);
  }

  Future<void> _pickSku(_PartRow row) async {
    final selected = await showModalBottomSheet<InventoryLookupItem>(
      context: context,
      isScrollControlled: true,
      builder: (context) => const _SkuLookupSheet(),
    );
    if (selected == null) return;
    setState(() {
      row.skuController.text = selected.sku;
    });
  }

  @override
  void dispose() {
    for (final r in _rows) {
      r.dispose();
    }
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Parts usage')),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          Text(
            'Each line must match a SKU in inventory. Unknown SKUs return HTTP 400.',
            style: Theme.of(context).textTheme.bodySmall?.copyWith(
                  color: Theme.of(context).colorScheme.onSurfaceVariant,
                ),
          ),
          const SizedBox(height: 12),
          ...List.generate(
            _rows.length,
            (i) => Padding(
              padding: const EdgeInsets.only(bottom: 12),
              child: Row(
                children: [
                  Expanded(
                    flex: 2,
                    child: TextField(
                      controller: _rows[i].skuController,
                      decoration: const InputDecoration(
                        labelText: 'SKU',
                        border: OutlineInputBorder(),
                      ),
                    ),
                  ),
                  IconButton(
                    tooltip: 'Search SKU',
                    onPressed: _busy ? null : () => _pickSku(_rows[i]),
                    icon: const Icon(Icons.search),
                  ),
                  const SizedBox(width: 8),
                  Expanded(
                    child: TextField(
                      controller: _rows[i].qtyController,
                      decoration: const InputDecoration(
                        labelText: 'Qty',
                        border: OutlineInputBorder(),
                      ),
                      keyboardType: const TextInputType.numberWithOptions(
                        decimal: true,
                      ),
                      inputFormatters: [
                        FilteringTextInputFormatter.allow(RegExp(r'[0-9.]')),
                      ],
                    ),
                  ),
                  IconButton(
                    icon: const Icon(Icons.remove_circle_outline),
                    onPressed: _rows.length <= 1
                        ? null
                        : () {
                            setState(() {
                              _rows[i].dispose();
                              _rows.removeAt(i);
                            });
                          },
                  ),
                ],
              ),
            ),
          ),
          TextButton.icon(
            onPressed: _busy
                ? null
                : () {
                    setState(() => _rows.add(_PartRow()));
                  },
            icon: const Icon(Icons.add),
            label: const Text('Add line'),
          ),
          if (_error != null)
            Padding(
              padding: const EdgeInsets.only(bottom: 12),
              child: Text(
                _error!,
                style: TextStyle(color: Theme.of(context).colorScheme.error),
              ),
            ),
          FilledButton(
            onPressed: _busy ? null : _submit,
            child: Text(_busy ? 'Submitting…' : 'Submit parts usage'),
          ),
        ],
      ),
    );
  }
}

class _PartRow {
  _PartRow()
      : skuController = TextEditingController(),
        qtyController = TextEditingController(text: '1');

  final TextEditingController skuController;
  final TextEditingController qtyController;

  void dispose() {
    skuController.dispose();
    qtyController.dispose();
  }
}

class _SkuLookupSheet extends ConsumerStatefulWidget {
  const _SkuLookupSheet();

  @override
  ConsumerState<_SkuLookupSheet> createState() => _SkuLookupSheetState();
}

class _SkuLookupSheetState extends ConsumerState<_SkuLookupSheet> {
  final _query = TextEditingController();
  bool _busy = false;
  String? _error;
  List<InventoryLookupItem> _items = const [];

  @override
  void initState() {
    super.initState();
    _search();
  }

  @override
  void dispose() {
    _query.dispose();
    super.dispose();
  }

  Future<void> _search() async {
    setState(() {
      _busy = true;
      _error = null;
    });
    try {
      final rows = await ref.read(inventoryLookupRepositoryProvider).searchItems(
            query: _query.text.trim(),
          );
      if (!mounted) return;
      setState(() => _items = rows);
    } catch (e) {
      if (!mounted) return;
      setState(() => _error = e.toString());
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return SafeArea(
      child: Padding(
        padding: EdgeInsets.only(
          left: 16,
          right: 16,
          top: 16,
          bottom: 16 + MediaQuery.of(context).viewInsets.bottom,
        ),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Text(
              'Find inventory SKU',
              style: Theme.of(context).textTheme.titleMedium,
            ),
            const SizedBox(height: 12),
            Row(
              children: [
                Expanded(
                  child: TextField(
                    controller: _query,
                    decoration: const InputDecoration(
                      labelText: 'Search SKU or name',
                      border: OutlineInputBorder(),
                    ),
                    onSubmitted: (_) => _search(),
                  ),
                ),
                const SizedBox(width: 8),
                FilledButton(
                  onPressed: _busy ? null : _search,
                  child: const Text('Search'),
                ),
              ],
            ),
            const SizedBox(height: 12),
            if (_busy) const LinearProgressIndicator(),
            if (_error != null)
              Padding(
                padding: const EdgeInsets.only(top: 8),
                child: Text(
                  _error!,
                  style: TextStyle(color: Theme.of(context).colorScheme.error),
                ),
              ),
            Flexible(
              child: ListView.builder(
                shrinkWrap: true,
                itemCount: _items.length,
                itemBuilder: (context, i) {
                  final it = _items[i];
                  return ListTile(
                    title: Text(it.sku),
                    subtitle: Text('${it.name} · on-hand ${it.onHandQuantity} ${it.unitOfMeasure}'),
                    onTap: () => Navigator.of(context).pop(it),
                  );
                },
              ),
            ),
          ],
        ),
      ),
    );
  }
}
