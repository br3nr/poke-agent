import express from 'express';
import { Dex } from '@pkmn/dex';

const app = express();
const port = 3000;
app.get('/pokemon', (req, res) => {
    const pokemon = req.query.pokemon;
    if (!pokemon) return res.status(400).json({ error: 'Must provide pokemon in query' });

    const species = Dex.species.get(pokemon);
    if (!species) return res.status(404).json({ error: `'${pokemon}' not found` });

    res.json({
        name: species.name,
        types: species.types,
        baseStats: species.baseStats,
        abilities: species.abilities,
        weight: species.weightkg
    });
});

app.get('/ability', (req, res) => {
    const ability = req.query.ability;
    if (!ability) return res.status(400).json({ error: 'Must provide ability in query' });

    const abilityData = Dex.abilities.get(ability);
    if (!abilityData) return res.status(404).json({ error: `'${ability}' not found` });

    res.json({
        desc: abilityData.desc,
        shortDesc: abilityData.shortDesc,
        flags: abilityData.flags,
    });
});

app.get('/move', (req, res) => {
    const move = req.query.move;
    if (!move) return res.status(400).json({ error: 'Must provide move in query' });

    const moveData = Dex.moves.get(move);
    if (!moveData) return res.status(404).json({ error: `'${move}' not found` });

    res.json({
        accuracy: moveData.accuracy,
        basePower: moveData.basePower,
        category: moveData.category,
        moveName: moveData.name,
        pp: moveData.pp,
        flags: moveData.flags,
        critRatio: moveData.critRatio,
        type: moveData.type,
        desc: moveData.desc,
        shortDesc: moveData.shortDesc,
        condition: moveData.condition,
        priority: moveData.priority,
        isZ: moveData.isZ
    });
});

app.listen(port, () => {
    console.log(`running at http://localhost:${port}`);
});

