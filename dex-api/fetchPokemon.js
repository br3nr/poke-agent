import { Dex } from '@pkmn/dex';

async function getPokemonDetails(pokemonNames) {
    for (const pokemonName of pokemonNames) {
        const species = Dex.species.get(pokemonName);
        
        if (!species) {
            console.log(`Pokemon '${pokemonName}' not found.`);
            continue;
        }
        
        console.log(`\nName: ${species.name}`);
        console.log(`Types: ${species.types.join(', ')}`);
        console.log(`Base Stats:`, species.baseStats);
        console.log(`Abilities:`, Object.values(species.abilities).join(', '));
    }
}

const pokemonList = [
    'Unown-M',
    'Furfrou-Pharaoh',
    'Rotom-Mow',
    'Vivillon-Polar',
    'Rotom-Wash',
    'Rotom-Heat',
    'Rotom-Frost',
    'Rotom-Fan',
    'Meowstic'
];

getPokemonDetails(pokemonList);
