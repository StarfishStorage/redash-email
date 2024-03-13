const puppeteer = require('puppeteer');
const {
    setTimeout,
} = require('node:timers/promises');

function usage() {
    console.log('usage: save-report.js --url redash_url --output report.pdf ' +
                            '[--param value] [--param value]');
    process.exit(1);
}

/* Argument parsing */
let redashUrl;
let outputFile;
let renderDelay;
const params = {};

for (let i=2; i < process.argv.length; i++) {
    switch (process.argv[i]) {
        case '--url':
            redashUrl = process.argv[++i];
            break;
        case '--delay':
            renderDelay = parseFloat(process.argv[++i]);
            break;
        case '--output':
            outputFile = process.argv[++i];
            break;
        case '--param':
            const kv = process.argv[++i].split('=', 2);
            params[kv[0]] = kv[1];
            break;
        default:
            usage();
    }
}
if (!redashUrl || !outputFile) {
    usage();
}

/* Utility Functions */

function replaceParams(pageUrl, params) {
    const url = new URL(pageUrl);
    const qs = url.searchParams;

    for (const [key, value] of Object.entries(params)) {
        qs.set('p_' + key, value);
    }
    url.search = qs.toString();
    return url.toString();
}

/* Main */

(async () => {
    /* Set viewport to a width that will result in two columns */
    const browser = await puppeteer.launch({
        defaultViewport: null,
        args: ['--ignore-certificate-errors', '--window-size=1500,1500', '--no-sandbox'],
        headless: 'new',
    });
    const page = await browser.newPage();

    const timeoutSec = 300;
    page.setDefaultNavigationTimeout(timeoutSec * 1000);
    page.setDefaultTimeout(timeoutSec * 1000);

    /* Fetch page and wait for redirects */
    await page.goto(redashUrl, {
        waitUntil: 'networkidle0',
    });

    /* Set "Dashboard" level parameters */
    if (params) {
        await page.goto(replaceParams(page.url(), params), {
            waitUntil: 'networkidle0',
        });
    }

    await page.evaluate((params) => {
        function removeElementsByClass(className) {
            const elements = document.getElementsByClassName(className);
            while (elements.length > 0) {
                elements[0].parentNode.removeChild(elements[0]);
            }
        }

        function formatDate(date) {
            return date.toLocaleDateString('en', {year: 'numeric', day: 'numeric',
                month: 'long'});
        }

        /* Remove input boxes */
        removeElementsByClass('ant-input-number-handler-wrap');
        removeElementsByClass('ant-select-arrow');

        /* Remove interactive interface from charts */
        removeElementsByClass('hoverlayer');
        removeElementsByClass('zoomlayer');
        removeElementsByClass('modebar-container');

        /* Remove table sorting buttons */
        removeElementsByClass('ant-table-column-sorter');

        /* Remove refreshed-at timesamp */
        removeElementsByClass('visible-print');

        /* Replace branding added by public URL */
        document.getElementById('footer').innerHTML = `
        <img src="/img/logo.png" height="40">
        `;

        /* Style tewaks */
        const style = document.createElement('style');
        style.innerHTML = `
        @page {
            margin: 1cm;
        }
        div.body-container {
            border: 1pt solid #333;
            border-radius: 2pt;
        }
        `;
        document.head.appendChild(style);

        /* Add date to heading */
        const todayDiv = document.createElement('div');
        todayDiv.className='page-header-wrapper';
        todayDiv.innerText = 'Generated on ' + formatDate(new Date());

        /* Replace dropdown search inputs with text inputs */
        const container = document.getElementsByClassName('parameter-container')[0];
        for (const param in params) {
            for (const labelElement of container.getElementsByTagName('label')) {
                if (labelElement.innerText.toLowerCase() == param) {
                    labelElement.parentElement.nextElementSibling.innerHTML = `
                      <div class="parameter-input" data-test="ParameterValueInput">
                        <input class="ant-input" aria-label="Parameter text value"
                               data-test="TextParamInput" type="text" value="${params[param]}">
                      </div>
                    `;
                }
            }
        }

        /* Add fake top-level parameter inputs if not found */
        const paramBlock = document.getElementsByClassName('parameter-block')[0];
        for (const param in params) {
            if (!paramBlock.innerHTML.includes('-' + param)) {
                paramBlock.innerHTML += `
                <div style="padding-left: 1em;" class="parameter-block">
                  <div class="di-block">
                    <div class="parameter-heading">
                      <label>${param}</label>
                    </div>
                    <div class="parameter-input">
                      <input class="ant-input" value="${params[param]}">
                    </div>
                  </div>
                </div>
                `;
            }
        }

        /* Remove apply button, if visible */
        const applyButton = document.getElementsByClassName('parameter-apply-button')[0];
        if (applyButton) {
            applyButton.remove();
        }

        const headerDiv = document.getElementsByClassName('page-header-wrapper')[0];
        headerDiv.insertAdjacentElement('afterend', todayDiv);
    }, params);

    /* wait for spinners to disappear */
    await page.waitForSelector('.spinner', {hidden: true});

    if (renderDelay) {
        await setTimeout(renderDelay * 1000);
    }

    await page.pdf({
        path: outputFile,
        width: '11in',
        height: '17in',
        displayHeaderFooter: false,
        scale: 0.9,
    });
    await browser.close();
})();
