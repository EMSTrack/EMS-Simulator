from ems.run import Driver


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Load configurations, data, preprocess models. Run simulator on "
                    "ambulance dispatch. Decisions are made during the simulation, but "
                    "the events are output to a csv file for replay.")

    parser.add_argument('config_file',
                        help="The simulator needs a configuration to begin the computation.",
                        type=str, )

    parser.add_argument('output_dir',
                        help="The simulator needs a configuration to begin the computation.",
                        type=str,
                        default=".")

    # parse arguments
    args = parser.parse_args()

    # create simulator
    driver = Driver(args.config_file)
    sim, data = driver.create_simulator()

    # run simulator
    sim.run()

    # Save the finished simulator information
    sim.write_results(output_dir=args.output_dir)
