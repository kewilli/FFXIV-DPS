using System;
using System.Collections.Generic;
using GeneticSharp.Domain.Chromosomes;
using GeneticSharp.Domain.Fitnesses;

namespace GeneticSearchAlgorithm
{
    public class PotencyFitness : IFitness
    {
        const double ManaTickTiming = 3;

        double IFitness.Evaluate(IChromosome chromosome)
        {
            return RunFitness(chromosome, false);
        }

        public double RunFitness(IChromosome chromosome, bool print)
        {
            double time = 0;
            double nextManaTick = 0;
            double totalPotency = 0;
            Status s = new Status(3, 3);

            Dictionary<string, double> coolDowns = new Dictionary<string, double>();

            Rotation rotation = (Rotation)chromosome;

            // MP regen tick! (Don't forget Umbral Ice! 1: 32%, 2: 47%, 3: 62% of total!)
            for (int i = 0; i < rotation.Length; i++)
            {
                var ability = (Ability)(rotation.GetGene(i).Value);

                //
                // TODO: No mana regen while in Astral Fire!!
                //

                // Do we have more mana to play with?
                if (time > nextManaTick && s.AstralFire == 0)
                {
                    while (time > nextManaTick)
                    {
                        s.Mp = Math.Min(s.Mp + s.MpRegenTick(), Status.MaxMp);
                        nextManaTick += ManaTickTiming;
                    }
                }

                var mpCost = ability.MpCost(s);
                double endOfCooldown;
                if (s.Mp >= mpCost && (!coolDowns.TryGetValue(ability.Name, out endOfCooldown) || endOfCooldown <= time))
                {
                    // Costs!
                    s.Mp -= mpCost;
                    s.Tp -= ability.TpCost;
                    coolDowns[ability.Name] = time + ability.Cooldown;
                    
                    // Damage
                    double newPotency = ability.Potency(s);
                    totalPotency += newPotency;

                    // Status changes
                    ability.StatusEffect(s);

                    // Increment the clock
                    time += ability.CastTime;

                    // Debug
                    if (print)
                    {
                        Console.WriteLine($"{ability.Name, 10} +{newPotency,4} = {totalPotency.ToString("######.##"),8}; Time + {ability.CastTime,4} = {time,5}; {s.ToString()}");
                    }
                }
                else
                {
                    // You failed!
                    time += 5.0;

                    if (print)
                    {
                        Console.WriteLine($"{ability.Name,10} - Failed to cast!");
                    }
                }
            }

            double dps = totalPotency / time;

            if (print)
            {
                Console.WriteLine($"{totalPotency} damage / {time} time = {dps}");
            }

            return time > 60 ? dps : 0;
        }
    }
}
