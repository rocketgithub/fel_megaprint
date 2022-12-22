# fel_megaprint

```python
AdendaDetail = etree.SubElement(Adenda, "AdendaDetail", id="AdendaSummary")
AdendaSummary = etree.SubElement(AdendaDetail, "AdendaSummary")
Valor1 = etree.SubElement(AdendaSummary, "Valor1")
Valor1.text = factura.comment or ""
```
