# Country Wiki Index

Direct references to `_shared/data/country_kb/` — loaded on demand.

## Entity Pages (Countries)

- [Australia](../country_kb/australia.md): australia, oceania, pacific
- [Brazil](../country_kb/brazil.md): brazil, south america, latin america
- [Canada](../country_kb/canada.md): canada, north america
- [China](../country_kb/china.md): china, asia, east asia
- [Egypt](../country_kb/egypt.md): egypt, africa, middle east
- [France](../country_kb/france.md): france, europe, western europe
- [Germany](../country_kb/germany.md): germany, europe, western europe
- [India](../country_kb/india.md): india, asia, south asia
- [Indonesia](../country_kb/indonesia.md): indonesia, asia, southeast asia
- [Italy](../country_kb/italy.md): italy, europe, southern europe
- [Japan](../country_kb/japan.md): japan, asia, east asia, bullet train, shinkansen
- [Mexico](../country_kb/mexico.md): mexico, north america, latin america
- [Nigeria](../country_kb/nigeria.md): nigeria, africa, west africa
- [Russia](../country_kb/russia.md): russia, europe, asia
- [Saudi Arabia](../country_kb/saudi_arabia.md): saudi arabia, middle east, gulf
- [South Africa](../country_kb/south_africa.md): south africa, africa, southern africa
- [South Korea](../country_kb/south_korea.md): south korea, korea, asia, east asia
- [Spain](../country_kb/spain.md): spain, europe, southern europe
- [United Kingdom](../country_kb/united_kingdom.md): uk, united kingdom, britain, europe
- [United States](../country_kb/united_states.md): usa, united states, america, north america

## Usage

```python
wiki_read("japan")      # Exact match
wiki_read("east asia")  # Keyword match → returns Japan, China, South Korea
wiki_read("bullet train")  # Keyword match → returns Japan
```