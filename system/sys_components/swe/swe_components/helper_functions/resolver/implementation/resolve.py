class resolve:
    def resolve_prompt(self):
        pass
    def resolve_sources(self):
        pass
    def resolve_inputs(self, udd: Path) -> Sequence[ResolvedInputs]: 
        pass
if __name__ == "__main__":
    resolve()
    print("Resolver executed")