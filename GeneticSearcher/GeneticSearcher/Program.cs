using System;
using GeneticSearchAlgorithm;
using GeneticSharp.Domain.Selections;
using GeneticSharp.Domain.Crossovers;
using GeneticSharp.Domain.Mutations;
using GeneticSharp.Domain.Populations;
using GeneticSharp.Domain;
using GeneticSharp.Domain.Terminations;
using GeneticSharp.Domain.Reinsertions;

namespace GeneticSearcher
{
    class Program
    {
        static void Main(string[] args)
        {
            var selection = new EliteSelection();
            //var crossover = new OnePointCrossover();
            //var crossover = new CutAndSpliceCrossover();
            var crossover = new TwoPointCrossover();
            var mutation = new TworsMutation();
            var fitness = new PotencyFitness();
            var chromosome = new Rotation();
            var population = new Population(50, 70, chromosome);

            var ga = new GeneticAlgorithm(population, fitness, selection, crossover, mutation);
            ga.Termination = new GenerationNumberTermination(10000);
            //ga.Termination = new FitnessStagnationTermination(10000);
            ga.Reinsertion = new ElitistReinsertion();

            Console.WriteLine("Running...");
            ga.Start();

            Console.WriteLine($"Best solution found has {ga.BestChromosome.Fitness} PPS.");

            fitness.RunFitness(ga.BestChromosome, true);

            Console.ReadLine();
        }
    }
}
