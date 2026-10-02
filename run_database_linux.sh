#!/bin/bash

# ============================================================
# Lake Kivu CTD Database Launcher
# ============================================================

# Move to project root
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR" || exit 1

PYTHON_PATH_FILE="$SCRIPT_DIR/python_path.txt"
PYTHON_PATH=""


# ============================================================
# 1. CHECK SAVED PYTHON PATH
# ============================================================

if [ -f "$PYTHON_PATH_FILE" ]; then

    SAVED_PYTHON=$(cat "$PYTHON_PATH_FILE")

    if [ -f "$SAVED_PYTHON" ] && [ -x "$SAVED_PYTHON" ]; then

        PYTHON_PATH="$SAVED_PYTHON"

        echo "Using saved Python environment:"
        echo "$PYTHON_PATH"
        echo

    else

        echo "The saved Python executable was not found."
        echo
    fi
fi


# ============================================================
# 2. FIND PYTHON IF NO VALID SAVED PATH
# ============================================================

if [ -z "$PYTHON_PATH" ]; then

    echo "Searching for Python environments..."
    echo

    CANDIDATES=()


    # --------------------------------------------------------
    # Python available through PATH
    # --------------------------------------------------------

    for CMD in python3 python; do

        FOUND=$(command -v "$CMD" 2>/dev/null)

        if [ -n "$FOUND" ]; then
            CANDIDATES+=("$FOUND")
        fi

    done


    # --------------------------------------------------------
    # Conda environments
    # --------------------------------------------------------

    if command -v conda >/dev/null 2>&1; then

        CONDA_BASE=$(conda info --base 2>/dev/null)

        if [ -n "$CONDA_BASE" ]; then

            # Base environment
            if [ -x "$CONDA_BASE/bin/python" ]; then
                CANDIDATES+=("$CONDA_BASE/bin/python")
            fi

        fi


        # Other Conda environments
        while IFS= read -r ENV_PATH; do

            if [ -n "$ENV_PATH" ]; then

                if [ -x "$ENV_PATH/bin/python" ]; then
                    CANDIDATES+=("$ENV_PATH/bin/python")
                fi

            fi

        done < <(
            conda env list 2>/dev/null |
            awk '!/^#/ && NF >= 2 {print $NF}'
        )

    fi


    # ========================================================
    # 3. REMOVE DUPLICATES
    # ========================================================

    UNIQUE_CANDIDATES=()

    for CANDIDATE in "${CANDIDATES[@]}"; do

        FOUND=false

        for EXISTING in "${UNIQUE_CANDIDATES[@]}"; do

            if [ "$CANDIDATE" = "$EXISTING" ]; then
                FOUND=true
                break
            fi

        done

        if [ "$FOUND" = false ]; then
            UNIQUE_CANDIDATES+=("$CANDIDATE")
        fi

    done


    COUNT=${#UNIQUE_CANDIDATES[@]}


    # ========================================================
    # 4. NO PYTHON FOUND
    # ========================================================

    if [ "$COUNT" -eq 0 ]; then

        echo "No Python executable was found automatically."
        echo
        echo "Please enter the full path to your Python executable."
        echo

        while true; do

            read -p "Python path: " PYTHON_PATH

            if [ -f "$PYTHON_PATH" ] && [ -x "$PYTHON_PATH" ]; then
                break
            fi

            echo
            echo "The specified file does not exist or is not executable."
            echo

        done

    fi


    # ========================================================
    # 5. ONLY ONE PYTHON FOUND
    # ========================================================

    if [ "$COUNT" -eq 1 ]; then

        PYTHON_PATH="${UNIQUE_CANDIDATES[0]}"

        echo "One Python executable was found:"
        echo
        echo "$PYTHON_PATH"
        echo

    fi


    # ========================================================
    # 6. MULTIPLE PYTHON EXECUTABLES FOUND
    # ========================================================

    if [ "$COUNT" -gt 1 ]; then

        echo "Several Python executables were found."
        echo
        echo "Please select the Python environment to use:"
        echo

        for i in "${!UNIQUE_CANDIDATES[@]}"; do

            NUMBER=$((i + 1))

            echo "[$NUMBER] ${UNIQUE_CANDIDATES[$i]}"

        done

        MANUAL_OPTION=$((COUNT + 1))

        echo "[$MANUAL_OPTION] Enter a Python path manually"
        echo


        while true; do

            read -p "Selection: " SELECTION


            # ------------------------------------------------
            # Manual path
            # ------------------------------------------------

            if [ "$SELECTION" -eq "$MANUAL_OPTION" ] 2>/dev/null; then

                echo
                read -p "Enter full path to Python executable: " PYTHON_PATH

                if [ -f "$PYTHON_PATH" ] && [ -x "$PYTHON_PATH" ]; then
                    break
                fi

                echo
                echo "The specified file does not exist or is not executable."
                echo

                continue

            fi


            # ------------------------------------------------
            # Normal selection
            # ------------------------------------------------

            if [[ "$SELECTION" =~ ^[0-9]+$ ]] &&
               [ "$SELECTION" -ge 1 ] &&
               [ "$SELECTION" -le "$COUNT" ]; then

                PYTHON_PATH="${UNIQUE_CANDIDATES[$((SELECTION - 1))]}"

                break

            fi


            echo
            echo "Invalid selection."
            echo "Please enter one of the numbers shown above."
            echo

        done

    fi


    # ========================================================
    # 7. SAVE PYTHON PATH
    # ========================================================

    echo "$PYTHON_PATH" > "$PYTHON_PATH_FILE"

    echo
    echo "Python environment saved to:"
    echo "$PYTHON_PATH_FILE"
    echo

fi


# ============================================================
# 8. START DATABASE INTERFACE
# ============================================================

echo "Starting Lake Kivu CTD database interface..."
echo "Python: $PYTHON_PATH"
echo

"$PYTHON_PATH" -m scripts.database_interface

echo
echo "Database interface closed."

read -p "Press Enter to close..."
