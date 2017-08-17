using System;
using System.Collections.Generic;

namespace GeneticSearchAlgorithm
{
    /// <summary>
    /// Defines an ability
    /// </summary>
    public sealed class Ability
    {
        public Ability(string name, Func<Status, int> mpCost, int tpCost, AbilityType type, int level, double cooldown, double castTime, Action<Status> statusEffect, Func<Status, int> potency)
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

        public Func<Status, int> Potency { get; }
    }

    public enum AbilityType
    {
        Ability,
        Spell
    }

    public static class BlmAbilities
    {
        static BlmAbilities()
        {
            Blizzard = new Ability(
            nameof(Blizzard),
            s => PotencyHelper.IceMp(s, Status.MaxMp / 12),
            0,
            AbilityType.Spell,
            1,
            2.5,
            2.5,
            s => s.IncreaseUmbralIce(),
            s => PotencyHelper.IcePotency(s, 100));

            Fire = new Ability(
            nameof(Fire),
            s => PotencyHelper.FireMp(s, Status.MaxMp / 12),
            0,
            AbilityType.Spell,
            2,
            2.5,
            2.5,
            s => s.IncreaseAstralFire(),
            s => PotencyHelper.FirePotency(s, 100));

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

            AllAbilities = new List<Ability>()
            {
                Blizzard,
                Fire,
                Transpose
            };
        }

        public static List<Ability> AllAbilities;

        public static Ability Blizzard;
        public static Ability Fire;
        public static Ability Transpose;
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
            switch (s.AstralFire)
            {
                case 0:
                    switch (s.UmbralIce)
                    {
                        case 0:
                            return baseMpCost;
                        case 1:
                            return baseMpCost / 2;
                        case 2:
                        case 3:
                            return baseMpCost / 4;
                        default:
                            throw new Exception("oops!");
                    }
                case 1:
                case 2:
                case 3:
                    return baseMpCost * 2;
                default:
                    throw new Exception("oops!!!");
            }
        }

        public static int FirePotency(Status s, int basePotency)
        {
            switch (s.AstralFire)
            {
                case 0:
                    switch (s.UmbralIce)
                    {
                        case 0:
                            return basePotency;
                        case 1:
                            return (int)(basePotency * 0.9);
                        case 2:
                            return (int)(basePotency * 0.8);
                        case 3:
                            return (int)(basePotency * 0.7);
                        default:
                            throw new Exception("oooooops!");

                    }
                case 1:
                    return (int)(basePotency * 1.4);
                case 2:
                    return (int)(basePotency * 1.6);
                case 3:
                    return (int)(basePotency * 1.8);
                default:
                    throw new Exception("Oops! Astral Fire should always be between 0 and 3, but found " + s.AstralFire);
            }
        }

        public static int IceMp(Status s, int baseMpCost)
        {
            switch (s.UmbralIce)
            {
                case 0:
                    switch (s.AstralFire)
                    {
                        case 0:
                            return baseMpCost;
                        case 1:
                            return baseMpCost / 2;
                        case 2:
                        case 3:
                            return baseMpCost / 4;
                        default:
                            throw new Exception("Oops! Umbral Ice should always be between 0 and 3, but found " + s.UmbralIce);
                    }
                case 1:
                case 2:
                case 3:
                    return baseMpCost;
                default:
                    throw new Exception("Ooops!");
            }
        }

        public static int IcePotency(Status s, int basePotency)
        {
            switch (s.UmbralIce)
            {
                case 0:
                    switch (s.AstralFire)
                    {
                        case 0:
                            return basePotency;
                        case 1:
                            return (int)(basePotency * 0.9);
                        case 2:
                            return (int)(basePotency * 0.8);
                        case 3:
                            return (int)(basePotency * 0.7);
                        default:
                            throw new Exception("Oops! Astral Fire should always be between 0 and 3, but found " + s.UmbralIce);
                    }
                case 1:
                    return (int)(basePotency * 0.9);
                case 2:
                    return (int)(basePotency * 0.8);
                case 3:
                    return (int)(basePotency * 0.7);
                default:
                    throw new Exception("Oops! Umbral Ice should always be between 0 and 3, but found " + s.UmbralIce);
            }
        }
    }
}
