using System;

namespace GeneticSearchAlgorithm
{
    public class Status
    {
        public const int MaxMp = 2156;
        public const int MaxTp = 100;

        private int m_umbralIce;
        private int m_astralFire;
        private readonly int m_maxUmbralIce;
        private readonly int m_maxAstralFire;

        public Status(int maxUmbralIce = 1, int maxAstralFire = 1)
        {
            m_maxAstralFire = maxAstralFire;
            m_maxUmbralIce = maxUmbralIce;
            m_umbralIce = 0;
            m_astralFire = 0;
            Mp = MaxMp;
            Tp = MaxTp;
        }

        public int UmbralIce => m_umbralIce;

        public int AstralFire => m_astralFire;

        public int Mp { get; set; }

        public int Tp { get; set; }

        public void IncreaseAstralFire()
        {
            if (m_umbralIce != 0)
            {
                m_umbralIce = 0;
            }
            else if (m_astralFire < m_maxAstralFire)
            {
                m_astralFire++;
            }
        }

        public void IncreaseUmbralIce()
        {
            if (m_astralFire != 0)
            {
                m_astralFire = 0;
            }
            else if (m_umbralIce < m_maxUmbralIce)
            {
                m_umbralIce++;
            }
        }

        /// <summary>
        /// Swap stacks to a specific value on the other side
        /// </summary>
        public void SwapIceFire(int newValue = 1)
        {
            if (m_umbralIce > 0)
            {
                m_umbralIce = 0;
                m_astralFire = newValue;
            }
            else if (m_astralFire > 0)
            {
                m_astralFire = 0;
                m_umbralIce = newValue;
            }
        }

        public int MpRegenTick()
        {
            if (m_umbralIce > 0)
            {
                if (m_umbralIce == 1)
                {
                    return (int)(Status.MaxMp * 0.32);
                }
                else if (m_umbralIce == 2)
                {
                    return (int)(Status.MaxMp * 0.47);
                }
                else if (m_umbralIce == 3)
                {
                    return (int)(Status.MaxMp * 0.62);
                }
                else
                {
                    throw new AstralFireUmbralIceException(m_umbralIce, true);
                }
            }
            else
            {
                // Base regen
                return (int)(Status.MaxMp * 0.02);
            }
        }

        public override string ToString()
        {
            return $"MP: {Mp,4}, TP: {Tp,4}, Fire: {AstralFire}, Ice: {UmbralIce}";
        }
    }
}
