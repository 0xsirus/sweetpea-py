
RED='\033[0;31m'
NC='\033[0m' # No Color
GREEN='\033[0;32m'
PURPLE='\033[0;35m'

if [ $# -eq 1 ];
then
    base=$1
else
    base=""
fi

#regenerate the tests!!
stack build
stack exec cnf

for file in generated_tests/$base*.cnf;
do
    if [ ! -e $file ]; then
        echo "No test found matching generated_tests/$base*.cnf"
        exit 1†s
    fi

    file=${file%.*}
    name=${file#generated_tests/}


    diff "$file.sol" <(cryptominisat5_simple "$file.cnf" | tail -n 2) > /dev/null

    if [ $? -ne 0 ];
    then

        echo -e "Oh no, ${RED}$name Failed! ${NC}\n    ${GREEN}TRUE${NC}                                                          ${PURPLE}GENERATED${NC}"
        diff -y "$file.sol" <(cryptominisat5_simple "$file.cnf" | tail -n 2)
        echo ""
      #  exit 1
    fi

done

echo -e "${GREEN}Done running tests!${NC}"
