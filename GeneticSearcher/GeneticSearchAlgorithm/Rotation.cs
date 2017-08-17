using GeneticSharp.Domain.Chromosomes;
using GeneticSharp.Domain.Randomizations;

namespace GeneticSearchAlgorithm
{
    public class Rotation : ChromosomeBase
    {
        public static readonly int MaxValue = 2;
        private int abilityCount = BlmAbilities.AllAbilities.Count;

        public Rotation() : base(100)
        {
            CreateGenes();
        }

        public override IChromosome CreateNew()
        {
            return new Rotation();
        }

        public override Gene GenerateGene(int geneIndex)
        {
            return new Gene(BlmAbilities.AllAbilities[RandomizationProvider.Current.GetInt(0, abilityCount)]);
        }
    }
}
