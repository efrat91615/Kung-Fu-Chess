import io
import unittest

from KungFuChess.board import Board
from KungFuChess.board_formatter import BoardFormatter
from KungFuChess.board_reader import BoardReader
from KungFuChess.board_validator import BoardValidator
from KungFuChess.invalid_board_exception import InvalidBoardException


class BoardFlowTests(unittest.TestCase):
    def test_read_validate_and_format_returns_canonical_board(self) -> None:
        input_stream = io.StringIO("wK . bQ\n. wN .\nbP . wR")
        reader = BoardReader(input_stream)
        validator = BoardValidator()
        formatter = BoardFormatter()

        rows = reader.read_board()
        validator.validate(rows)
        board = Board(rows)

        self.assertEqual(3, len(board.rows))
        self.assertEqual(3, board.columns)
        self.assertEqual("wK . bQ\n. wN .\nbP . wR", formatter.format(board))

    def test_validator_rejects_rows_with_different_lengths(self) -> None:
        validator = BoardValidator()
        with self.assertRaisesRegex(InvalidBoardException, 'ERROR ROW_WIDTH_MISMATCH'):
            validator.validate([['wK', '.', 'bQ'], ['wK', '.']])

    def test_validator_rejects_rows_with_invalid_characters(self) -> None:
        validator = BoardValidator()
        with self.assertRaisesRegex(InvalidBoardException, 'ERROR UNKNOWN_TOKEN'):
            validator.validate([['wX'], ['.']])

    def test_validator_rejects_unknown_token_in_board_input(self) -> None:
        validator = BoardValidator()
        with self.assertRaisesRegex(InvalidBoardException, 'ERROR UNKNOWN_TOKEN'):
            validator.validate([['wK', 'xZ'], ['.', '.']])

    def test_validator_rejects_row_width_mismatch_in_board_input(self) -> None:
        validator = BoardValidator()
        with self.assertRaisesRegex(InvalidBoardException, 'ERROR ROW_WIDTH_MISMATCH'):
            validator.validate([['wK', '.', '.'], ['.', 'bK']])


if __name__ == "__main__":
    unittest.main()
