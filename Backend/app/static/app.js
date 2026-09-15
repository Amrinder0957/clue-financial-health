const $ = id => document.getElementById(id);


/* =====================================================
   ELEMENTS
===================================================== */

const landing = $("landing");
const app = $("app");

const uploadScreen = $("uploadScreen");
const loadingScreen = $("loadingScreen");
const resultsScreen = $("resultsScreen");

const fileInput = $("fileInput");
const dropzone = $("dropzone");
const selectedFile = $("selectedFile");
const analyzeBtn = $("analyzeBtn");
const statusText = $("status");

const languageSelect = $("languageSelect");

const reductionSlider = $("reductionSlider");
const reductionValue = $("reductionValue");
const simulateBtn = $("simulateBtn");

let latestAnalysis = null;


/* =====================================================
   LANDING
===================================================== */

function startApp() {
    landing.classList.add("hidden");
    app.classList.remove("hidden");

    showScreen(uploadScreen);

    history.pushState({
        page: "app"
    }, "", "#app");

    window.scrollTo({
        top: 0,
        behavior: "smooth"
    });
}


$("startBtn").onclick = startApp;
$("heroStart").onclick = startApp;


$("homeBtn").onclick = e => {
    e.preventDefault();

    goHome();

    history.pushState({
        page: "home"
    }, "", "#home");
};

/* =====================================================
   HOME + BROWSER BACK
===================================================== */

function goHome() {
    app.classList.add("hidden");
    landing.classList.remove("hidden");

    window.scrollTo({
        top: 0,
        behavior: "smooth"
    });
}

const navHome = $("navHome");

if (navHome) {
    navHome.onclick = e => {
        e.preventDefault();

        goHome();

        history.pushState({
            page: "home"
        }, "", "#home");
    };
}


/* Browser back button */
window.addEventListener("popstate", () => {
    goHome();
});

$("newAnalysis").onclick = () => {

    latestAnalysis = null;

    resultsScreen.classList.add("hidden");
    uploadScreen.classList.remove("hidden");

    fileInput.value = "";

    selectedFile.classList.add("hidden");

    statusText.textContent = "";
};


/* =====================================================
   SCREEN FLOW
===================================================== */

function showScreen(screen) {

    [
        uploadScreen,
        loadingScreen,
        resultsScreen
    ].forEach(x => {

        if (x) {
            x.classList.add("hidden");
        }

    });

    if (screen) {
        screen.classList.remove("hidden");
    }

}


/* =====================================================
   FILE SELECTION
===================================================== */

fileInput.addEventListener("change", () => {

    const file = fileInput.files[0];

    if (!file) return;

    if (!file.name.toLowerCase().endsWith(".csv")) {

        statusText.textContent =
            "Please select a CSV file.";

        fileInput.value = "";

        return;
    }

    selectedFile.textContent =
        `✓ ${file.name}`;

    selectedFile.classList.remove("hidden");

    statusText.textContent = "";
});


/* =====================================================
   DRAG & DROP
===================================================== */

dropzone.addEventListener("dragover", e => {

    e.preventDefault();

    dropzone.style.borderColor = "#2878d7";
});


dropzone.addEventListener("dragleave", () => {

    dropzone.style.borderColor = "";
});


dropzone.addEventListener("drop", e => {

    e.preventDefault();

    dropzone.style.borderColor = "";

    const file = e.dataTransfer.files[0];

    if (
        !file ||
        !file.name.toLowerCase().endsWith(".csv")
    ) {

        statusText.textContent =
            "Please select a CSV file.";

        return;
    }

    fileInput.files = e.dataTransfer.files;

    selectedFile.textContent =
        `✓ ${file.name}`;

    selectedFile.classList.remove("hidden");

    statusText.textContent = "";
});


/* =====================================================
   ANALYSIS
===================================================== */

analyzeBtn.onclick = async () => {

    const file = fileInput.files[0];

    if (!file) {

        statusText.textContent =
            "Please choose a CSV file.";

        return;
    }


    analyzeBtn.disabled = true;

    statusText.textContent = "";

    showScreen(loadingScreen);

    runLoadingAnimation();


    const formData = new FormData();

    formData.append("file", file);


    try {

        const response = await fetch(
            "/analyses",
            {
                method: "POST",
                body: formData
            }
        );


        const data = await response.json();


        if (!response.ok) {

            throw new Error(
                data.detail ||
                "Analysis failed."
            );
        }


        latestAnalysis = data;


        await new Promise(
            resolve =>
                setTimeout(resolve, 900)
        );


        displayResults(data);

        showScreen(resultsScreen);


    } catch (error) {

        showScreen(uploadScreen);

        statusText.textContent =
            error.message;


    } finally {

        analyzeBtn.disabled = false;
    }
};


/* =====================================================
   LOADING ANIMATION
===================================================== */

async function runLoadingAnimation() {

    const steps = [
        $("step1"),
        $("step2"),
        $("step3"),
        $("step4"),
        $("step5")
    ];


    steps.forEach(step => {

        if (step) {
            step.classList.remove("done");
        }

    });


    for (const step of steps) {

        if (!step) continue;

        await new Promise(
            resolve =>
                setTimeout(resolve, 350)
        );


        step.textContent =
            step.textContent.replace(
                "○",
                "✓"
            );


        step.classList.add("done");
    }
}


/* =====================================================
   DISPLAY RESULTS
===================================================== */

function displayResults(data) {

    const score =
        Number(data.score || 0);


    $("score").textContent =
        score;


    $("band").textContent =
        data.band || "--";


    $("provisional").textContent =
        data.provisional
            ? "Provisional Score — based on available transaction history."
            : "Based on the uploaded transaction data.";


    /* ---------------- PILLARS ---------------- */

    $("cashScore").textContent =
        data.cash_flow_score ?? "--";


    $("anomalyScore").textContent =
        data.anomaly_score ?? "--";


    $("creditScore").textContent =
        data.credit_debt_score ?? "--";


    setProgress(
        "cashBar",
        data.cash_flow_score
    );


    setProgress(
        "anomalyBar",
        data.anomaly_score
    );


    setProgress(
        "creditBar",
        data.credit_debt_score
    );


    /* ---------------- MAIN SCORE ---------------- */

    setScoreColor(
        $("scoreCircle"),
        score
    );


    setTextColor(
        $("band"),
        score
    );


    /* ---------------- PREDICTION ---------------- */

    const prediction =
        data.prediction || {};


    const trend =
        prediction.trend ||
        "INSUFFICIENT_DATA";


    $("trend").textContent =
        trend;


    $("cashTrend").textContent =
        trend;


    const runway =
        formatRunway(
            prediction.runway_days
        );


    $("runway").textContent =
        runway;


    $("cashRunway").textContent =
        runway;


    $("warning").textContent =
        prediction.warning || "";


    /* ---------------- DEBT ---------------- */

    $("debtLargeScore").textContent =
        data.credit_debt_score ?? "--";


    /* ---------------- RISKS ---------------- */

    renderRisks(
        data.risks || []
    );


    /* ---------------- CASH GRAPH ---------------- */

    renderCashGraph(
        prediction,
        data
    );


    /* ---------------- WHAT-IF RESET ---------------- */

    if ($("simulationResult")) {

        $("simulationResult")
            .classList.add("hidden");
    }


    if ($("simulationMessage")) {

        $("simulationMessage")
            .textContent = "";
    }


    /* ---------------- DEFAULT TAB ---------------- */

    switchTab("overview");
}


/* =====================================================
   DYNAMIC CASH FLOW GRAPH
===================================================== */

function renderCashGraph(prediction, data) {

    const container =
        document.querySelector(".cash-visual");


    if (!container) return;


    const trend =
        String(
            prediction.trend ||
            "INSUFFICIENT_DATA"
        ).toUpperCase();


    const score =
        Number(
            data.cash_flow_score ?? 50
        );


    const overallScore =
        Number(
            data.score ?? 50
        );


    /*
       We create a visual trend representation
       from the actual CLUE analysis result.

       This is NOT pretending to be a
       day-by-day historical balance chart.
    */


    let points;


    if (trend === "IMPROVING") {

        points =
            "20,105 75,96 130,91 185,80 240,75 295,64 350,58 405,48 460,42 520,30";


    } else if (trend === "DETERIORATING") {

        points =
            "20,35 75,43 130,48 185,60 240,67 295,76 350,82 405,91 460,98 520,110";


    } else if (trend === "STABLE") {

        points =
            "20,72 75,70 130,73 185,71 240,74 295,72 350,73 405,71 460,74 520,72";


    } else {

        points =
            "20,70 75,66 130,73 185,68 240,74 295,69 350,72 405,67 460,73 520,69";
    }


    /*
       Slightly adjust the vertical position
       using the actual score so different
       datasets don't produce an identical visual.
    */

    const offset =
        Math.round(
            (50 - score) * 0.12
        );


    const adjustedPoints =
        points
            .split(" ")
            .map(point => {

                const parts =
                    point.split(",");

                const x =
                    Number(parts[0]);

                const y =
                    Number(parts[1]) + offset;

                return `${x},${y}`;
            })
            .join(" ");


    /*
       Color follows the CLUE health system:
       green = good
       yellow = watch
       orange = strained
       red = critical
    */

    let lineColor;


    if (overallScore >= 80) {

        lineColor = "#159447";

    } else if (overallScore >= 60) {

        lineColor = "#d99b00";

    } else if (overallScore >= 40) {

        lineColor = "#e56d16";

    } else {

        lineColor = "#d83b3b";
    }


    container.innerHTML = `

        <svg
            viewBox="0 0 540 135"
            width="100%"
            height="150"
            preserveAspectRatio="none"
            aria-label="Cash flow trend"
        >

            <line
                x1="0"
                y1="120"
                x2="540"
                y2="120"
                stroke="#d8e0e8"
                stroke-width="1"
            />

            <polyline
                points="${adjustedPoints}"
                fill="none"
                stroke="${lineColor}"
                stroke-width="3"
                stroke-linecap="round"
                stroke-linejoin="round"
            />

        </svg>
    `;
}


/* =====================================================
   SCORE COLORS
===================================================== */

function setScoreColor(
    element,
    score
) {

    if (!element) return;


    let color;


    if (score >= 80) {

        color = "#159447";

    } else if (score >= 60) {

        color = "#d99b00";

    } else if (score >= 40) {

        color = "#e56d16";

    } else {

        color = "#d83b3b";
    }


    element.style.background =
        `conic-gradient(
            ${color} ${score}%,
            #e6ebf0 ${score}%
        )`;
}


function setTextColor(
    element,
    score
) {

    if (!element) return;


    if (score >= 80) {

        element.style.color =
            "#159447";

    } else if (score >= 60) {

        element.style.color =
            "#d99b00";

    } else if (score >= 40) {

        element.style.color =
            "#e56d16";

    } else {

        element.style.color =
            "#d83b3b";
    }
}


function setProgress(
    id,
    value
) {

    const bar = $(id);

    if (
        !bar ||
        value == null
    ) {
        return;
    }


    const score =
        Number(value);


    bar.style.width =
        `${Math.max(
            0,
            Math.min(100, score)
        )}%`;


    if (score >= 80) {

        bar.style.background =
            "#159447";

    } else if (score >= 60) {

        bar.style.background =
            "#d99b00";

    } else if (score >= 40) {

        bar.style.background =
            "#e56d16";

    } else {

        bar.style.background =
            "#d83b3b";
    }
}


/* =====================================================
   RISKS
===================================================== */

function renderRisks(risks) {

    const container =
        $("riskList");


    if (!container) return;


    container.innerHTML = "";


    if (!risks.length) {

        container.innerHTML = `

            <div class="risk low">

                <strong>
                    ✓ No significant risks detected
                </strong>

                <p>
                    The uploaded data did not trigger
                    major risk indicators.
                </p>

            </div>
        `;

        return;
    }


    risks.forEach(risk => {

        const severity =
            String(
                risk.severity ||
                "LOW"
            ).toLowerCase();


        const div =
            document.createElement("div");


        div.className =
            `risk ${severity}`;


        const title =
            escapeHtml(
                risk.title ||
                "Risk detected"
            );


        const explanation =
            escapeHtml(
                risk.explanation ||
                ""
            );


        div.innerHTML = `

            <strong>
                ${escapeHtml(
            risk.severity ||
            "LOW"
        )}
                ·
                ${title}
            </strong>

            <p>
                ${explanation}
            </p>
        `;


        container.appendChild(div);
    });
}


/* =====================================================
   TABS
===================================================== */

document
    .querySelectorAll(".tab")
    .forEach(tab => {

        tab.addEventListener(
            "click",
            () => {

                switchTab(
                    tab.dataset.tab
                );

            }
        );

    });


function switchTab(name) {

    document
        .querySelectorAll(".tab")
        .forEach(tab => {

            tab.classList.toggle(
                "active",
                tab.dataset.tab === name
            );

        });


    document
        .querySelectorAll(".tab-content")
        .forEach(section => {

            section.classList.toggle(
                "active",
                section.id === name
            );

        });
}


/* =====================================================
   WHAT-IF SLIDER
===================================================== */

if (reductionSlider) {

    reductionSlider.addEventListener(
        "input",
        () => {

            reductionValue.textContent =
                reductionSlider.value;

        }
    );
}


/* =====================================================
   WHAT-IF SIMULATION
===================================================== */

if (simulateBtn) {

    simulateBtn.onclick =
        async () => {

            if (!latestAnalysis) {

                $("simulationMessage").textContent =
                    "Please analyze a CSV first.";

                return;
            }


            simulateBtn.disabled = true;

            simulateBtn.textContent =
                "Calculating...";


            try {

                /*
                   Load the saved analysis.
                   This guarantees that What-If uses
                   the actual values generated from
                   the uploaded CSV.
                */

                const response =
                    await fetch(
                        `/analyses/${latestAnalysis.analysis_id}`
                    );


                const saved =
                    await response.json();


                if (!response.ok) {

                    throw new Error(
                        saved.detail ||
                        "Unable to load analysis."
                    );
                }


                const report =
                    saved.report || {};


                const prediction =
                    report.prediction || {};


                const currentBalance =
                    Number(
                        prediction.current_balance
                    );


                const inflow =
                    Number(
                        prediction.average_daily_inflow
                    );


                const outflow =
                    Number(
                        prediction.average_daily_outflow
                    );


                if (
                    !Number.isFinite(
                        currentBalance
                    ) ||
                    !Number.isFinite(
                        inflow
                    ) ||
                    !Number.isFinite(
                        outflow
                    )
                ) {

                    throw new Error(
                        "Scenario data is not available for this analysis."
                    );
                }


                const reduction =
                    Number(
                        reductionSlider.value
                    );


                const response2 =
                    await fetch(
                        "/what-if",
                        {
                            method: "POST",

                            headers: {
                                "Content-Type":
                                    "application/json"
                            },

                            body:
                                JSON.stringify({

                                    current_balance:
                                        currentBalance,

                                    average_daily_inflow:
                                        inflow,

                                    average_daily_outflow:
                                        outflow,

                                    reduction_percent:
                                        reduction
                                })
                        }
                    );


                const result =
                    await response2.json();


                if (!response2.ok) {

                    throw new Error(
                        result.detail ||
                        "Scenario calculation failed."
                    );
                }


                displaySimulation(
                    result
                );


            } catch (error) {

                $("simulationMessage")
                    .textContent =
                    error.message;


            } finally {

                simulateBtn.disabled = false;

                simulateBtn.textContent =
                    "Run Scenario →";
            }

        };
}


/* =====================================================
   DISPLAY WHAT-IF RESULT
===================================================== */
/* =====================================================
   DISPLAY WHAT-IF RESULT
===================================================== */

function displaySimulation(
    result
) {
    const resultBox =
        $("simulationResult");

    if (resultBox) {
        resultBox.classList.remove(
            "hidden"
        );
    }


    /* ---------------- RUNWAY VALUES ---------------- */

    const originalRunway =
        result.original_runway_days;

    const scenarioRunway =
        result.scenario_runway_days;


    $("currentRunway").textContent =
        formatRunway(
            originalRunway
        );

    $("scenarioRunway").textContent =
        formatRunway(
            scenarioRunway
        );


    /* ---------------- IMPROVEMENT ---------------- */

    const originalIsInfinite =
        originalRunway === "infinite" ||
        originalRunway === Infinity;

    const scenarioIsInfinite =
        scenarioRunway === "infinite" ||
        scenarioRunway === Infinity;


    let improvementText;


    /*
       Both are infinite:
       The business is already sustainable.
    */

    if (
        originalIsInfinite &&
        scenarioIsInfinite
    ) {
        improvementText =
            "Already sustainable";
    }


    /*
       Finite runway becomes infinite:
       This is a significant improvement.
    */

    else if (
        scenarioIsInfinite &&
        !originalIsInfinite
    ) {
        improvementText =
            "Significant";
    }


    /*
       Both are finite:
       Calculate the actual difference.
    */

    else {
        const original =
            Number(
                originalRunway
            );

        const scenario =
            Number(
                scenarioRunway
            );


        if (
            !Number.isFinite(original) ||
            !Number.isFinite(scenario)
        ) {
            improvementText =
                "No improvement";
        }

        else {
            const improvement =
                scenario - original;


            /*
               0 → 0
            */

            if (
                Math.abs(improvement) < 0.05
            ) {
                improvementText =
                    "No improvement";
            }


            /*
               Positive improvement
               Example: 10 → 18
            */

            else if (
                improvement > 0
            ) {
                improvementText =
                    `+${improvement.toFixed(1)} days`;
            }


            /*
               Negative improvement
               Example: 20 → 15
            */

            else {
                improvementText =
                    `${improvement.toFixed(1)} days`;
            }
        }
    }


    $("runwayImprovement")
        .textContent =
        improvementText;


    /* ---------------- DESCRIPTION ---------------- */

    $("simulationMessage")
        .textContent =
        result.description || "";
}


/* =====================================================
   HELPERS
===================================================== */

function formatRunway(value) {

    if (
        value === "infinite" ||
        value === Infinity
    ) {

        return "Infinite";
    }


    if (
        value === null ||
        value === undefined ||
        !Number.isFinite(
            Number(value)
        )
    ) {

        return "Not available";
    }


    return `${Number(value).toFixed(1)} days`;
}


function escapeHtml(value) {

    return String(value)

        .replaceAll(
            "&",
            "&amp;"
        )

        .replaceAll(
            "<",
            "&lt;"
        )

        .replaceAll(
            ">",
            "&gt;"
        )

        .replaceAll(
            '"',
            "&quot;"
        )

        .replaceAll(
            "'",
            "&#039;"
        );
}


/* =====================================================
   LANGUAGE
===================================================== */

const ui = {

    en: {

        start:
            "Check Financial Health",

        analyze:
            "Analyze with CLUE →",

        upload:
            "Upload your business transactions."
    },


    hi: {

        start:
            "वित्तीय स्वास्थ्य जांचें",

        analyze:
            "CLUE से विश्लेषण करें →",

        upload:
            "अपने व्यवसाय के लेन-देन अपलोड करें।"
    },


    te: {

        start:
            "ఆర్థిక ఆరోగ్యాన్ని తనిఖీ చేయండి",

        analyze:
            "CLUEతో విశ్లేషించండి →",

        upload:
            "మీ వ్యాపార లావాదేవీలను అప్లోడ్ చేయండి."
    }
};


if (languageSelect) {

    languageSelect.addEventListener(
        "change",
        () => {

            const language =
                languageSelect.value;


            const text =
                ui[language];


            if (!text) return;


            $("startBtn").textContent =
                text.start;


            $("heroStart").innerHTML =
                `${text.start} <span>→</span>`;


            $("analyzeBtn").textContent =
                text.analyze;


            const uploadHeading =
                document.querySelector(
                    "#uploadScreen h1"
                );


            if (uploadHeading) {

                uploadHeading.textContent =
                    text.upload;
            }

        }
    );
}