using System;
using System.Collections.Generic;

namespace GeneticSearchAlgorithm
{
    /// <summary>
    /// Defines an ability
    /// </summary>
    public sealed class Ability
    {
        public Ability(string name, Func<Status, int> mpCost, int tpCost, AbilityType type, int level, double cooldown, double castTime, Action<Status> statusEffect, Func<Status, double> potency)
        {
            Name = name;
            MpCost = mpCost;
            TpCost = tpCost;
            Type = type;
            Level = level;
            Cooldown = cooldown;
            CastTime = castTime;
            StatusEffect = statusEffect;
            Potency = potency;
        }

        /// <summary>
        /// Visible name
        /// </summary>
        public string Name { get; }

        /// <summary>
        /// Mana cost
        /// </summary>
        public Func<Status, int> MpCost { get; }

        /// <summary>
        /// TP (??) cost
        /// </summary>
        public int TpCost { get; }

        /// <summary>
        /// Type of the ability
        /// </summary>
        public AbilityType Type { get; }

        /// <summary>
        /// Level when this is unlocked
        /// </summary>
        public int Level { get; }

        /// <summary>
        /// Time until available after use
        /// </summary>
        public double Cooldown { get; }

        /// <summary>
        /// Time to use ability
        /// </summary>
        public double CastTime { get; }

        /// <summary>
        /// Updates the Status (buffs)
        /// </summary>
        public Action<Status> StatusEffect { get; }

        public Func<Status, double> Potency { get; }
    }

    public enum AbilityType
    {
        Ability,
        Instant,
        Spell
    }

    public static class BlmAbilities
    {
        static BlmAbilities()
        {
            Blizzard = new Ability(
                nameof(Blizzard),
                s => PotencyHelper.IceMp(s, 66),
                0,
                AbilityType.Spell,
                1,
                2.5,
                2.5,
                s => s.IncreaseUmbralIce(),
                s => PotencyHelper.IcePotency(s, 180));

            Fire = new Ability(
                nameof(Fire),
                s => PotencyHelper.FireMp(s, 167),
                0,
                AbilityType.Spell,
                2,
                2.5,
                2.5,
                s => s.IncreaseAstralFire(),
                s => PotencyHelper.FirePotency(s, 180));

            Transpose = new Ability(
                nameof(Transpose),
                s => 0,
                0,
                AbilityType.Ability,
                4,
                12,
                0.75,
                s => s.SwapIceFire(1),
                s => 0);

            Scathe = new Ability(
                nameof(Scathe),
                s => 143,
                0,
                AbilityType.Ability,
                15,
                2.5,
                2.5,
                s => { return; },
                s => 120); // 100 80%, 200 20%

            AllAbilities = new List<Ability>()
            {
                Blizzard,
                Fire,
                Transpose,
                Scathe
            };
        }

        public static List<Ability> AllAbilities;

        public static Ability Blizzard;
        public static Ability Fire;
        public static Ability Transpose;
        public static Ability Scathe;
    }

    public static class PotencyHelper
    {
        /// <summary>
        /// 200% MP if Astral Fire > 0
        /// 50% MP if Umbral Ice == 1
        /// 25% MP if Umbral Ice >= 2
        /// </summary>
        public static int FireMp(Status s, int baseMpCost)
        {
            if (s.AstralFire == 0)
            {
                if (s.UmbralIce == 0)
                    return baseMpCost;
                else if (s.UmbralIce == 1)
                    return baseMpCost / 2;
                else if (s.UmbralIce == 2 || s.UmbralIce == 3)
                    return baseMpCost / 4;
                else
                    throw new AstralFireUmbralIceException(s.UmbralIce, true);
            }
            else if (s.AstralFire <= 3)
                return baseMpCost * 2;
            else
                throw new AstralFireUmbralIceException(s.AstralFire, false);
        }

        public static double FirePotency(Status s, int basePotency)
        {
            if (s.AstralFire == 0)
            {
                if (s.UmbralIce == 0)
                    return basePotency;
                else if (s.UmbralIce == 1)
                    return basePotency * 0.9;
                else if (s.UmbralIce == 2)
                    return basePotency * 0.8;
                else if (s.UmbralIce == 3)
                    return basePotency * 0.7;
                else
                    throw new AstralFireUmbralIceException(s.UmbralIce, true);
            }
            else if (s.AstralFire == 1)
                return basePotency * 1.4;
            else if (s.AstralFire == 2)
                return basePotency * 1.6;
            else if (s.AstralFire == 3)
                return basePotency * 1.8;
            else
                throw new AstralFireUmbralIceException(s.AstralFire, false);
        }

        public static int IceMp(Status s, int baseMpCost)
        {
            if (s.UmbralIce == 0)
            {
                if (s.AstralFire == 0)
                    return baseMpCost;
                else if (s.AstralFire == 1)
                    return baseMpCost / 2;
                else if (s.AstralFire == 2 || s.AstralFire == 3)
                    return baseMpCost / 4;
                else
                    throw new AstralFireUmbralIceException(s.AstralFire, false);
            }
            else if (s.UmbralIce <= 3)
                return baseMpCost;
            else
                throw new AstralFireUmbralIceException(s.UmbralIce, true);
        }

        public static double IcePotency(Status s, int basePotency)
        {
            if (s.UmbralIce == 0)
            {
                if (s.AstralFire == 0)
                    return basePotency;
                else if (s.AstralFire == 1)
                    return basePotency * 0.9;
                else if (s.AstralFire == 2)
                    return basePotency * 0.8;
                else if (s.AstralFire == 3)
                    return basePotency * 0.7;
                else
                    throw new AstralFireUmbralIceException(s.AstralFire, false);
            }
            else if (s.UmbralIce <= 3)
                return basePotency;
            else
                throw new AstralFireUmbralIceException(s.UmbralIce, true);
        }
    }

    public class AstralFireUmbralIceException : Exception
    {
        public AstralFireUmbralIceException(int level, bool ice) : base($"{(ice ? "Umbral Ice" : "Astral Fire")} should always be between 0 and 3. Found " + level)
        {
        }
    }
}
