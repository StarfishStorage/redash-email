module.exports = {
    'env': {
        'browser': true,
        'es2021': true,
    },
    'extends': 'google',
    'overrides': [
    ],
    'parserOptions': {
        'ecmaVersion': 'latest',
        'sourceType': 'module',
    },
    'rules': {
        'indent': ['error', 4, {'SwitchCase': 1}],
        'require-jsdoc': ['off'],
        'max-len': ['warn', {'code': 110, 'tabWidth': 4}],
        'guard-for-in': ['off'],
    },
};
