import express from 'express';
import { Dex } from '@pkmn/dex';

const app = express();
const port = 3000;

app.get('/pokemon', (req, res) => {
    const name = req.query.name;
    if (!name) return res.status(400).json({ error: 'Pls provide pokemon name in query' });

    const species = Dex.species.get(name);
    if (!species) return res.status(404).json({ error: `'${name}' not found` });

    res.json({
        name: species.name,
        types: species.types,
        baseStats: species.baseStats,
        abilities: species.abilities,
        weight: species.weightkg
    });
});

app.get('/move', (req, res) => {
    const name = req.query.name;
    if (!name) return res.status(400).json({ error: 'Pls provide move name in query' });

    const move = Dex.moves.get(name);
    if (!move) return res.status(404).json({ error: `'${name}' not found` });

    res.json({
        accuracy: move.accuracy,
        basePower: move.basePower,
        category: move.category,
        moveName: move.name,
        pp: move.pp,
        flags: move.flags,
        critRatio: move.critRatio,
        type: move.type,
        desc: move.desc,
        shortDesc: move.shortDesc,
        condition: move.condition,
        priority: move.priority,
        isZ: move.isZ
    });
});

app.listen(port, () => {
    console.log(`running at http://localhost:${port}`);
});

