# This shell script is used to download and process the microchip DFU's for
# distrubution with picchick. It downloads the device packs, extracts only the
# needed .ini files, then strips them of comments, empty lines, and SFR* config
# entries. This gets it down from ~56M to ~4.5M for PICs 10, 12, 16, and 18.

# List of DFPs to include (Latest of 2025-09-07)
PACKS=(\
	Microchip.PIC10-12Fxxx_DFP.1.8.184.atpack	\
	Microchip.PIC12-16Cxxx_DFP.1.7.175.atpack	\
	Microchip.PIC12-16F1xxx_DFP.1.8.254.atpack	\
	Microchip.PIC16F1xxxx_DFP.1.27.418.atpack	\
	Microchip.PIC16Fxxx_DFP.1.7.162.atpack		\
	Microchip.PIC18Cxxx_DFP.1.6.169.atpack		\
	Microchip.PIC18F-J_DFP.1.9.170.atpack		\
	Microchip.PIC18F-K_DFP.1.15.303.atpack		\
	Microchip.PIC18F-Q_DFP.1.28.451.atpack		\
	Microchip.PIC18Fxxxx_DFP.1.7.171.atpack		\
)

MCHIP_URL="https://packs.download.microchip.com"

DL_DIR="build/vendor/downloads"
PACK_DIR="build/vendor/packs"
INI_DIR="picchick/devices/ini"

work=0

for pack in "${PACKS[@]}"; do

    # Download .atpack if it doesn't exist
    mkdir -p "$DL_DIR"
    if [[ ! -f "$DL_DIR/$pack" ]]; then
        echo Downloading $pack ...
        curl -s "$MCHIP_URL/$pack" > "$DL_DIR/$pack"
        let work++
    fi

    # Extract .atpack into directory with same name
    pack_dir=$(basename "$pack" ".atpack")
    mkdir -p "$PACK_DIR"
    if [[ ! -d "$PACK_DIR/$pack_dir" ]]; then
        unzip "$DL_DIR/$pack" "xc8/pic/dat/ini/*" -d "$PACK_DIR/$pack_dir"
        let work++
    fi

done

INI_FILES=($(find "$PACK_DIR" -name "*.ini"))
mkdir -p "$INI_DIR"
for file in "${INI_FILES[@]}"; do
    if [[ ! -f "$INI_DIR/$(basename $file)" ]]; then
        echo Trimming "$INI_DIR/$(basename $file)" ...
        grep -vE "^#|^$" "$file" | grep -vE "^SFR" >  "$INI_DIR/$(basename $file)"
        let work++
    fi
done

LICENSE_SOURCE_FILE="10f200.ini"
LICENSE_FILE="$INI_DIR/LICENSE"
LICENSE_SOURCE_FILE_PATH=$(find "$PACK_DIR" -name "$LICENSE_SOURCE_FILE")
if [[ ! -f "$LICENSE_FILE" ]]; then
    echo Creating "$LICENSE_FILE" ...
    head -n 29 "$LICENSE_SOURCE_FILE_PATH" | tail -n +3 > "$LICENSE_FILE"
    let work++
fi

if [[ $work -eq 0 ]]; then
    echo "Nothing to do!"
fi

echo -n "Total size: "
du -h "$INI_DIR"