import express from 'express';
import { Dex } from '@pkmn/dex';

const app = express();
const PORT = 3000;

app.get('/pokemon/:name', (req, res) => {
    const pokemonName = req.params.name;
    const species = Dex.species.get(pokemonName);
    
    if (!species) {
        return res.status(404).json({ error: `Pokemon '${pokemonName}' not found.` });
    }
    
    res.json({
        name: species.name,
        types: species.types,
        baseStats: species.baseStats,
        abilities: Object.values(species.abilities)
    });
});

app.listen(PORT, () => {
    console.log(`Server running on http://localhost:${PORT}`);
});

